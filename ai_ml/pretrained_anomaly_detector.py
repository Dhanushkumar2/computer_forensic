"""
Pre-trained Anomaly Detection using GAT Model
Loads existing trained model and performs inference on forensic data
"""
import os
import sys
import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.neighbors import kneighbors_graph
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import GATConv
import warnings
warnings.filterwarnings("ignore")

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from ai_ml.feature_extractor import ForensicFeatureExtractor


class GAT(torch.nn.Module):
    """Graph Attention Network - Same architecture as in notebook"""
    def __init__(self, in_channels, hidden_channels=16, out_channels=2):
        super().__init__()
        self.g1 = GATConv(in_channels, hidden_channels, heads=8, dropout=0.4)
        self.g2 = GATConv(hidden_channels * 8, out_channels, heads=1, concat=False, dropout=0.4)
        self.dropout = torch.nn.Dropout(0.4)
    
    def forward(self, x, edge_index):
        x = F.elu(self.g1(x, edge_index))
        x = self.dropout(x)
        x = self.g2(x, edge_index)
        return x


class PretrainedForensicAnomalyDetector:
    """Forensic anomaly detection using pre-trained GAT model"""
    
    def __init__(self, model_path='/home/dhanush/myvenv/forensic_ir_app/dl_models/gat_best.pth', device=None):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = model_path
        self.feature_extractor = ForensicFeatureExtractor()
        self.scaler = StandardScaler()
        self.model = None
        
        print(f"Using device: {self.device}")
        print(f"Model path: {self.model_path}")
    
    def load_model(self, num_features=19, num_classes=2):
        """Load the pre-trained GAT model"""
        print("Loading pre-trained GAT model...")
        
        # Initialize model with same architecture
        self.model = GAT(num_features, 16, num_classes).to(self.device)
        
        # Load state dict
        try:
            state_dict = torch.load(self.model_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            self.model.eval()
            print("Model loaded successfully!")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def extract_and_prepare_data(self, case_id, k_neighbors=8):
        """
        Extract features from case and prepare for GAT inference
        
        Args:
            case_id: Case identifier
            k_neighbors: Number of neighbors for kNN graph
            
        Returns:
            torch_geometric.data.Data: Graph data object
            pandas.DataFrame: Original dataframe with features
        """
        print(f"Extracting features for case {case_id}...")
        
        # Extract features
        df = self.feature_extractor.extract_features_from_case(case_id)
        
        if df.empty:
            raise ValueError(f"No features extracted for case {case_id}")
        
        print(f"Extracted {len(df)} feature records")
        
        # Prepare features (same as in notebook)
        feature_columns = [
            'User_ID', 'Activity_Type', 'Resource_Accessed', 'Action',
            'Login_Attempts', 'File_Size', 'Hour', 'File_Info_Missing',
            'Login_Info_Missing', 'Action_Missing', 'Anomaly_Missing',
            'DayOfWeek', 'IsWeekend', 'IP1', 'IP2', 'IP3', 'IP4',
            'IsPrivateIP', 'File_Size_Log'
        ]
        
        X = df[feature_columns].values
        y = df['Anomaly_Label'].values if 'Anomaly_Label' in df.columns else np.zeros(len(df))
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Convert to tensors
        X_tensor = torch.tensor(X_scaled, dtype=torch.float32)
        y_tensor = torch.tensor(y, dtype=torch.long)
        
        # Build kNN graph (same as notebook)
        print(f"Building kNN graph with k={k_neighbors}...")
        knn_graph = kneighbors_graph(X_scaled, n_neighbors=k_neighbors, mode='connectivity', include_self=False)
        edge_index = torch.tensor(np.vstack(knn_graph.nonzero()), dtype=torch.long)
        
        # Create PyTorch Geometric data object
        data = Data(x=X_tensor, edge_index=edge_index, y=y_tensor)
        
        print(f"Graph created: {data.num_nodes} nodes, {data.num_edges} edges")
        print(f"Feature dimension: {data.num_node_features}")
        
        return data, df
    
    def predict_anomalies(self, case_id, k_neighbors=8, threshold=0.5):
        """
        Predict anomalies for a case using pre-trained model
        
        Args:
            case_id: Case identifier
            k_neighbors: Number of neighbors for kNN graph
            threshold: Anomaly threshold (0.5 = balanced)
            
        Returns:
            pandas.DataFrame: Predictions with anomaly scores
        """
        if self.model is None:
            if not self.load_model():
                raise ValueError("Failed to load model")
        
        # Extract and prepare data
        data, df = self.extract_and_prepare_data(case_id, k_neighbors)
        data = data.to(self.device)
        
        print("Running inference...")
        
        # Predict
        self.model.eval()
        with torch.no_grad():
            out = self.model(data.x, data.edge_index)
            probs = F.softmax(out, dim=1)
            preds = (probs[:, 1] > threshold).long()  # Use threshold for prediction
        
        # Add predictions to dataframe
        df['Predicted_Anomaly'] = preds.cpu().numpy()
        df['Anomaly_Score'] = probs[:, 1].cpu().numpy()  # Probability of being anomaly
        df['Normal_Score'] = probs[:, 0].cpu().numpy()   # Probability of being normal
        
        # Calculate statistics
        total_activities = len(df)
        predicted_anomalies = (df['Predicted_Anomaly'] == 1).sum()
        avg_anomaly_score = df['Anomaly_Score'].mean()
        max_anomaly_score = df['Anomaly_Score'].max()
        
        print(f"\n📊 PREDICTION RESULTS:")
        print(f"Total activities analyzed: {total_activities}")
        print(f"Predicted anomalies: {predicted_anomalies} ({predicted_anomalies/total_activities*100:.1f}%)")
        print(f"Average anomaly score: {avg_anomaly_score:.3f}")
        print(f"Maximum anomaly score: {max_anomaly_score:.3f}")
        
        return df
    
    def analyze_predictions(self, df, top_n=10):
        """
        Analyze and visualize prediction results
        
        Args:
            df: DataFrame with predictions
            top_n: Number of top anomalies to show
        """
        print(f"\n🔍 ANOMALY ANALYSIS:")
        
        # Get anomalies
        anomalies = df[df['Predicted_Anomaly'] == 1].copy()
        
        if len(anomalies) == 0:
            print("No anomalies detected!")
            return
        
        # Sort by anomaly score
        anomalies = anomalies.sort_values('Anomaly_Score', ascending=False)
        
        print(f"\n🚨 TOP {min(top_n, len(anomalies))} ANOMALIES:")
        print("-" * 80)
        
        for i, (_, row) in enumerate(anomalies.head(top_n).iterrows()):
            activity_type = self._get_activity_type_name(row['Activity_Type'])
            action = self._get_action_name(row['Action'])
            
            print(f"{i+1:2d}. Score: {row['Anomaly_Score']:.3f} | "
                  f"Activity: {activity_type:15s} | "
                  f"Action: {action:10s} | "
                  f"Hour: {row['Hour']:2.0f} | "
                  f"Weekend: {'Yes' if row['IsWeekend'] else 'No':3s}")
        
        # Anomaly distribution by activity type
        self._plot_anomaly_distribution(df)
        
        # Anomaly scores distribution
        self._plot_score_distribution(df)
        
        # Temporal analysis
        self._plot_temporal_analysis(df)
    
    def _get_activity_type_name(self, activity_type):
        """Convert activity type number to name"""
        activity_map = {
            0: 'Unknown',
            1: 'Browser History',
            2: 'Browser Cookies', 
            3: 'Browser Downloads',
            4: 'File Access',
            5: 'Program Execution',
            6: 'USB Connection',
            7: 'Registry Access',
            8: 'Network Connection',
            9: 'Login Attempt',
            10: 'File Deletion',
            11: 'System Event'
        }
        return activity_map.get(int(activity_type), 'Unknown')
    
    def _get_action_name(self, action):
        """Convert action number to name"""
        action_map = {
            0: 'Unknown',
            1: 'Read',
            2: 'Write', 
            3: 'Execute',
            4: 'Delete',
            5: 'Create',
            6: 'Modify',
            7: 'Access',
            8: 'Download',
            9: 'Upload',
            10: 'Connect',
            11: 'Disconnect',
            12: 'Login',
            13: 'Logout'
        }
        return action_map.get(int(action), 'Unknown')
    
    def _plot_anomaly_distribution(self, df):
        """Plot anomaly distribution by activity type"""
        plt.figure(figsize=(12, 6))
        
        # Count anomalies by activity type
        activity_counts = df.groupby(['Activity_Type', 'Predicted_Anomaly']).size().unstack(fill_value=0)
        
        # Convert activity type numbers to names
        activity_names = [self._get_activity_type_name(i) for i in activity_counts.index]
        activity_counts.index = activity_names
        
        # Plot stacked bar chart
        ax = activity_counts.plot(kind='bar', stacked=True, 
                                 color=['#2E86AB', '#F24236'],  # Blue for normal, red for anomaly
                                 figsize=(12, 6))
        
        plt.title('Anomaly Distribution by Activity Type', fontsize=14, fontweight='bold')
        plt.xlabel('Activity Type', fontsize=12)
        plt.ylabel('Count', fontsize=12)
        plt.legend(['Normal', 'Anomaly'], loc='upper right')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()
    
    def _plot_score_distribution(self, df):
        """Plot distribution of anomaly scores"""
        plt.figure(figsize=(12, 5))
        
        # Subplot 1: Histogram of anomaly scores
        plt.subplot(1, 2, 1)
        plt.hist(df['Anomaly_Score'], bins=50, alpha=0.7, color='#F24236', edgecolor='black')
        plt.axvline(0.5, color='black', linestyle='--', label='Threshold (0.5)')
        plt.title('Distribution of Anomaly Scores')
        plt.xlabel('Anomaly Score')
        plt.ylabel('Frequency')
        plt.legend()
        
        # Subplot 2: Box plot by prediction
        plt.subplot(1, 2, 2)
        normal_scores = df[df['Predicted_Anomaly'] == 0]['Anomaly_Score']
        anomaly_scores = df[df['Predicted_Anomaly'] == 1]['Anomaly_Score']
        
        plt.boxplot([normal_scores, anomaly_scores], 
                   labels=['Normal', 'Anomaly'],
                   patch_artist=True,
                   boxprops=dict(facecolor='lightblue'),
                   medianprops=dict(color='red', linewidth=2))
        
        plt.title('Anomaly Scores by Prediction')
        plt.ylabel('Anomaly Score')
        
        plt.tight_layout()
        plt.show()
    
    def _plot_temporal_analysis(self, df):
        """Plot temporal patterns of anomalies"""
        plt.figure(figsize=(15, 5))
        
        # Subplot 1: Anomalies by hour
        plt.subplot(1, 3, 1)
        hourly_anomalies = df.groupby(['Hour', 'Predicted_Anomaly']).size().unstack(fill_value=0)
        
        if 1 in hourly_anomalies.columns:
            plt.bar(hourly_anomalies.index, hourly_anomalies[1], 
                   color='#F24236', alpha=0.7, label='Anomalies')
        
        plt.title('Anomalies by Hour of Day')
        plt.xlabel('Hour')
        plt.ylabel('Count')
        plt.xticks(range(0, 24, 2))
        
        # Subplot 2: Anomalies by day of week
        plt.subplot(1, 3, 2)
        dow_anomalies = df.groupby(['DayOfWeek', 'Predicted_Anomaly']).size().unstack(fill_value=0)
        
        if 1 in dow_anomalies.columns:
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            plt.bar(range(7), [dow_anomalies.get(i, {}).get(1, 0) for i in range(7)], 
                   color='#F24236', alpha=0.7)
            plt.xticks(range(7), days)
        
        plt.title('Anomalies by Day of Week')
        plt.xlabel('Day')
        plt.ylabel('Count')
        
        # Subplot 3: Weekend vs Weekday
        plt.subplot(1, 3, 3)
        weekend_anomalies = df.groupby(['IsWeekend', 'Predicted_Anomaly']).size().unstack(fill_value=0)
        
        if 1 in weekend_anomalies.columns:
            labels = ['Weekday', 'Weekend']
            values = [weekend_anomalies.get(0, {}).get(1, 0), weekend_anomalies.get(1, {}).get(1, 0)]
            plt.bar(labels, values, color='#F24236', alpha=0.7)
        
        plt.title('Anomalies: Weekday vs Weekend')
        plt.ylabel('Count')
        
        plt.tight_layout()
        plt.show()
    
    def save_results(self, df, output_file):
        """Save prediction results to CSV"""
        # Select relevant columns for output
        output_columns = [
            'User_ID', 'Activity_Type', 'Action', 'Hour', 'DayOfWeek', 'IsWeekend',
            'File_Size', 'Login_Attempts', 'IP1', 'IP2', 'IP3', 'IP4', 'IsPrivateIP',
            'Predicted_Anomaly', 'Anomaly_Score', 'Normal_Score'
        ]
        
        # Add readable names
        df_output = df[output_columns].copy()
        df_output['Activity_Type_Name'] = df_output['Activity_Type'].apply(self._get_activity_type_name)
        df_output['Action_Name'] = df_output['Action'].apply(self._get_action_name)
        
        # Save to CSV
        df_output.to_csv(output_file, index=False)
        print(f"Results saved to: {output_file}")
    
    def close(self):
        """Close connections"""
        self.feature_extractor.close()


def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Forensic Anomaly Detection with Pre-trained GAT')
    parser.add_argument('case_id', help='Case ID to analyze')
    parser.add_argument('--model', default='/home/dhanush/myvenv/forensic_ir_app/dl_models/gat_best.pth', 
                       help='Path to pre-trained model')
    parser.add_argument('--threshold', type=float, default=0.5, 
                       help='Anomaly threshold (default: 0.5)')
    parser.add_argument('--k', type=int, default=8, 
                       help='Number of neighbors for kNN graph (default: 8)')
    parser.add_argument('--output', '-o', help='Output CSV file for results')
    parser.add_argument('--top', type=int, default=10, 
                       help='Number of top anomalies to display (default: 10)')
    
    args = parser.parse_args()
    
    # Initialize detector
    detector = PretrainedForensicAnomalyDetector(model_path=args.model)
    
    try:
        # Load model
        if not detector.load_model():
            print("Failed to load model. Exiting.")
            return
        
        # Predict anomalies
        print(f"\n🔍 Analyzing case: {args.case_id}")
        predictions = detector.predict_anomalies(args.case_id, k_neighbors=args.k, threshold=args.threshold)
        
        # Analyze results
        detector.analyze_predictions(predictions, top_n=args.top)
        
        # Save results if requested
        if args.output:
            detector.save_results(predictions, args.output)
        
        print(f"\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        detector.close()


if __name__ == '__main__':
    main()