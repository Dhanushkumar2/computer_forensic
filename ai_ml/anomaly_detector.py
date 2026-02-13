"""
Anomaly Detection using Graph Neural Networks
Integrates feature extraction with GCN/GAT models for forensic analysis
"""
import os
import sys
import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.neighbors import kneighbors_graph
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv, GATConv
import warnings
warnings.filterwarnings("ignore")

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from ai_ml.feature_extractor import ForensicFeatureExtractor


class GCN(torch.nn.Module):
    """Graph Convolutional Network for anomaly detection"""
    def __init__(self, in_channels, hidden_channels=64, out_channels=2):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, out_channels)
        self.dropout = torch.nn.Dropout(0.4)
    
    def forward(self, x, edge_index):
        x = F.relu(self.conv1(x, edge_index))
        x = self.dropout(x)
        x = self.conv2(x, edge_index)
        return x


class GAT(torch.nn.Module):
    """Graph Attention Network for anomaly detection"""
    def __init__(self, in_channels, hidden_channels=16, out_channels=2):
        super().__init__()
        self.conv1 = GATConv(in_channels, hidden_channels, heads=8, dropout=0.4)
        self.conv2 = GATConv(hidden_channels * 8, out_channels, heads=1, concat=False, dropout=0.4)
        self.dropout = torch.nn.Dropout(0.4)
    
    def forward(self, x, edge_index):
        x = F.elu(self.conv1(x, edge_index))
        x = self.dropout(x)
        x = self.conv2(x, edge_index)
        return x


class ForensicAnomalyDetector:
    """Main class for forensic anomaly detection"""
    
    def __init__(self, device=None):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.feature_extractor = ForensicFeatureExtractor()
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.models = {}
        
        print(f"Using device: {self.device}")
    
    def extract_and_prepare_data(self, case_id, k_neighbors=8):
        """
        Extract features from case and prepare for GNN training
        
        Args:
            case_id: Case identifier
            k_neighbors: Number of neighbors for kNN graph
            
        Returns:
            torch_geometric.data.Data: Graph data object
        """
        print(f"Extracting features for case {case_id}...")
        
        # Extract features
        df = self.feature_extractor.extract_features_from_case(case_id)
        
        if df.empty:
            raise ValueError(f"No features extracted for case {case_id}")
        
        print(f"Extracted {len(df)} feature records")
        
        # Prepare features
        feature_columns = [
            'User_ID', 'Activity_Type', 'Resource_Accessed', 'Action',
            'Login_Attempts', 'File_Size', 'Hour', 'File_Info_Missing',
            'Login_Info_Missing', 'Action_Missing', 'Anomaly_Missing',
            'DayOfWeek', 'IsWeekend', 'IP1', 'IP2', 'IP3', 'IP4',
            'IsPrivateIP', 'File_Size_Log'
        ]
        
        X = df[feature_columns].values
        y = df['Anomaly_Label'].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Convert to tensors
        X_tensor = torch.tensor(X_scaled, dtype=torch.float32)
        y_tensor = torch.tensor(y, dtype=torch.long)
        
        # Build kNN graph
        print(f"Building kNN graph with k={k_neighbors}...")
        knn_graph = kneighbors_graph(X_scaled, n_neighbors=k_neighbors, mode='connectivity', include_self=False)
        edge_index = torch.tensor(np.vstack(knn_graph.nonzero()), dtype=torch.long)
        
        # Create PyTorch Geometric data object
        data = Data(x=X_tensor, edge_index=edge_index, y=y_tensor)
        
        print(f"Graph created: {data.num_nodes} nodes, {data.num_edges} edges")
        print(f"Feature dimension: {data.num_node_features}")
        print(f"Classes: {len(torch.unique(y_tensor))}")
        
        return data, df
    
    def train_models(self, data, test_size=0.2, val_size=0.1, max_epochs=100, patience=10):
        """
        Train GCN and GAT models
        
        Args:
            data: PyTorch Geometric data object
            test_size: Test set proportion
            val_size: Validation set proportion
            max_epochs: Maximum training epochs
            patience: Early stopping patience
            
        Returns:
            dict: Training results
        """
        print("Preparing train/val/test splits...")
        
        # Create train/val/test masks
        num_nodes = data.num_nodes
        indices = np.arange(num_nodes)
        
        # Stratified split
        train_idx, test_idx = train_test_split(
            indices, test_size=test_size, 
            stratify=data.y.numpy(), random_state=42
        )
        
        train_idx, val_idx = train_test_split(
            train_idx, test_size=val_size/(1-test_size), 
            stratify=data.y.numpy()[train_idx], random_state=42
        )
        
        # Create masks
        data.train_mask = torch.zeros(num_nodes, dtype=torch.bool)
        data.val_mask = torch.zeros(num_nodes, dtype=torch.bool)
        data.test_mask = torch.zeros(num_nodes, dtype=torch.bool)
        
        data.train_mask[train_idx] = True
        data.val_mask[val_idx] = True
        data.test_mask[test_idx] = True
        
        data = data.to(self.device)
        
        print(f"Train: {len(train_idx)}, Val: {len(val_idx)}, Test: {len(test_idx)}")
        
        # Initialize models
        num_features = data.num_node_features
        num_classes = len(torch.unique(data.y))
        
        gcn_model = GCN(num_features, 64, num_classes).to(self.device)
        gat_model = GAT(num_features, 16, num_classes).to(self.device)
        
        # Train models
        results = {}
        
        print("\nTraining GCN...")
        gcn_results = self._train_single_model(gcn_model, data, "GCN", max_epochs, patience)
        results['GCN'] = gcn_results
        self.models['GCN'] = gcn_model
        
        print("\nTraining GAT...")
        gat_results = self._train_single_model(gat_model, data, "GAT", max_epochs, patience)
        results['GAT'] = gat_results
        self.models['GAT'] = gat_model
        
        return results, data
    
    def _train_single_model(self, model, data, model_name, max_epochs, patience):
        """Train a single model with early stopping"""
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=5e-4)
        
        best_val_acc = 0
        patience_counter = 0
        train_losses = []
        val_accs = []
        
        for epoch in range(1, max_epochs + 1):
            # Training
            model.train()
            optimizer.zero_grad()
            out = model(data.x, data.edge_index)
            loss = F.cross_entropy(out[data.train_mask], data.y[data.train_mask])
            loss.backward()
            optimizer.step()
            
            # Validation
            model.eval()
            with torch.no_grad():
                val_out = model(data.x, data.edge_index)
                val_pred = val_out.argmax(dim=1)
                val_acc = (val_pred[data.val_mask] == data.y[data.val_mask]).float().mean().item()
            
            train_losses.append(loss.item())
            val_accs.append(val_acc)
            
            # Early stopping
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                patience_counter = 0
                # Save best model state
                torch.save(model.state_dict(), f'best_{model_name.lower()}_model.pth')
            else:
                patience_counter += 1
            
            if epoch % 10 == 0:
                print(f"Epoch {epoch:03d}: Loss={loss:.4f}, Val Acc={val_acc:.4f}")
            
            if patience_counter >= patience:
                print(f"Early stopping at epoch {epoch}")
                break
        
        # Load best model
        model.load_state_dict(torch.load(f'best_{model_name.lower()}_model.pth'))
        
        # Test evaluation
        test_acc, test_pred, test_probs = self._evaluate_model(model, data, data.test_mask)
        
        return {
            'train_losses': train_losses,
            'val_accs': val_accs,
            'best_val_acc': best_val_acc,
            'test_acc': test_acc,
            'test_predictions': test_pred,
            'test_probabilities': test_probs
        }
    
    def _evaluate_model(self, model, data, mask):
        """Evaluate model on given mask"""
        model.eval()
        with torch.no_grad():
            out = model(data.x, data.edge_index)
            pred = out.argmax(dim=1)
            probs = F.softmax(out, dim=1)
            
            acc = (pred[mask] == data.y[mask]).float().mean().item()
            
            return acc, pred[mask].cpu().numpy(), probs[mask].cpu().numpy()
    
    def analyze_results(self, results, data, df):
        """Analyze and visualize results"""
        print("\n" + "="*50)
        print("ANOMALY DETECTION RESULTS")
        print("="*50)
        
        # Test accuracies
        for model_name, result in results.items():
            print(f"{model_name} Test Accuracy: {result['test_acc']:.4f}")
        
        # Confusion matrices
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        test_labels = data.y[data.test_mask].cpu().numpy()
        
        for i, (model_name, result) in enumerate(results.items()):
            cm = confusion_matrix(test_labels, result['test_predictions'])
            sns.heatmap(cm, annot=True, fmt='d', ax=axes[i], cmap='Blues')
            axes[i].set_title(f'{model_name} Confusion Matrix')
            axes[i].set_xlabel('Predicted')
            axes[i].set_ylabel('Actual')
        
        plt.tight_layout()
        plt.savefig('confusion_matrices.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Classification reports
        for model_name, result in results.items():
            print(f"\n{model_name} Classification Report:")
            print(classification_report(test_labels, result['test_predictions']))
        
        # Feature importance analysis
        self._analyze_anomalies(df, data)
    
    def _analyze_anomalies(self, df, data):
        """Analyze detected anomalies"""
        print("\n" + "="*50)
        print("ANOMALY ANALYSIS")
        print("="*50)
        
        # Anomaly distribution by activity type
        anomaly_by_activity = df.groupby(['Activity_Type', 'Anomaly_Label']).size().unstack(fill_value=0)
        
        plt.figure(figsize=(10, 6))
        anomaly_by_activity.plot(kind='bar', stacked=True)
        plt.title('Anomaly Distribution by Activity Type')
        plt.xlabel('Activity Type')
        plt.ylabel('Count')
        plt.legend(['Normal', 'Anomaly'])
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('anomaly_by_activity.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Anomaly distribution by hour
        anomaly_by_hour = df.groupby(['Hour', 'Anomaly_Label']).size().unstack(fill_value=0)
        
        plt.figure(figsize=(12, 6))
        anomaly_by_hour.plot(kind='bar', stacked=True)
        plt.title('Anomaly Distribution by Hour of Day')
        plt.xlabel('Hour')
        plt.ylabel('Count')
        plt.legend(['Normal', 'Anomaly'])
        plt.tight_layout()
        plt.savefig('anomaly_by_hour.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Top anomalous activities
        anomalies = df[df['Anomaly_Label'] == 1]
        if not anomalies.empty:
            print(f"\nDetected {len(anomalies)} anomalous activities:")
            print(f"- Late night activities: {len(anomalies[(anomalies['Hour'] >= 23) | (anomalies['Hour'] <= 5)])}")
            print(f"- Weekend activities: {len(anomalies[anomalies['IsWeekend'] == 1])}")
            print(f"- Large file operations: {len(anomalies[anomalies['File_Size'] > anomalies['File_Size'].quantile(0.95)])}")
            print(f"- External IP connections: {len(anomalies[anomalies['IsPrivateIP'] == 0])}")
    
    def predict_anomalies(self, case_id, model_name='GCN'):
        """
        Predict anomalies for a new case
        
        Args:
            case_id: Case identifier
            model_name: Model to use ('GCN' or 'GAT')
            
        Returns:
            pandas.DataFrame: Predictions with anomaly scores
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not trained yet")
        
        # Extract features
        data, df = self.extract_and_prepare_data(case_id)
        data = data.to(self.device)
        
        # Predict
        model = self.models[model_name]
        model.eval()
        
        with torch.no_grad():
            out = model(data.x, data.edge_index)
            probs = F.softmax(out, dim=1)
            preds = out.argmax(dim=1)
        
        # Add predictions to dataframe
        df['Predicted_Anomaly'] = preds.cpu().numpy()
        df['Anomaly_Score'] = probs[:, 1].cpu().numpy()  # Probability of being anomaly
        
        return df
    
    def save_models(self, save_dir='models'):
        """Save trained models"""
        os.makedirs(save_dir, exist_ok=True)
        
        for model_name, model in self.models.items():
            torch.save(model.state_dict(), f'{save_dir}/{model_name.lower()}_model.pth')
            print(f"Saved {model_name} model to {save_dir}/{model_name.lower()}_model.pth")
    
    def load_models(self, save_dir='models', num_features=19, num_classes=2):
        """Load trained models"""
        # Initialize models
        gcn_model = GCN(num_features, 64, num_classes).to(self.device)
        gat_model = GAT(num_features, 16, num_classes).to(self.device)
        
        # Load state dicts
        gcn_model.load_state_dict(torch.load(f'{save_dir}/gcn_model.pth', map_location=self.device))
        gat_model.load_state_dict(torch.load(f'{save_dir}/gat_model.pth', map_location=self.device))
        
        self.models['GCN'] = gcn_model
        self.models['GAT'] = gat_model
        
        print("Models loaded successfully")
    
    def close(self):
        """Close connections"""
        self.feature_extractor.close()


def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Forensic Anomaly Detection')
    parser.add_argument('case_id', help='Case ID to analyze')
    parser.add_argument('--train', action='store_true', help='Train new models')
    parser.add_argument('--predict', action='store_true', help='Predict anomalies only')
    parser.add_argument('--model', default='GCN', choices=['GCN', 'GAT'], help='Model to use for prediction')
    
    args = parser.parse_args()
    
    # Initialize detector
    detector = ForensicAnomalyDetector()
    
    try:
        if args.train:
            # Extract data and train models
            data, df = detector.extract_and_prepare_data(args.case_id)
            results, data = detector.train_models(data)
            
            # Analyze results
            detector.analyze_results(results, data, df)
            
            # Save models
            detector.save_models()
            
        elif args.predict:
            # Load models and predict
            detector.load_models()
            predictions = detector.predict_anomalies(args.case_id, args.model)
            
            # Show results
            anomalies = predictions[predictions['Predicted_Anomaly'] == 1]
            print(f"\nDetected {len(anomalies)} anomalies out of {len(predictions)} activities")
            
            if not anomalies.empty:
                print("\nTop 10 anomalies by score:")
                top_anomalies = anomalies.nlargest(10, 'Anomaly_Score')
                for _, row in top_anomalies.iterrows():
                    print(f"Score: {row['Anomaly_Score']:.3f} | Activity: {row['Activity_Type']} | Hour: {row['Hour']}")
        
        else:
            # Full pipeline
            data, df = detector.extract_and_prepare_data(args.case_id)
            results, data = detector.train_models(data)
            detector.analyze_results(results, data, df)
            detector.save_models()
    
    finally:
        detector.close()


if __name__ == '__main__':
    main()