"""
Model inference utilities for GAT-based anomaly detection.
"""

import os
import numpy as np
import torch
import torch.nn.functional as F
from sklearn.neighbors import kneighbors_graph
from torch_geometric.data import Data
from torch_geometric.nn import GATConv

from ai_ml.preprocessing import extract_features, preprocess_dataframe, FEATURE_COLUMNS


class GAT(torch.nn.Module):
    """Graph Attention Network - same architecture as training notebook."""

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


ACTIVITY_NAME = {
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
    11: 'System Event',
}

ACTION_NAME = {
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
    13: 'Logout',
}


def _build_knn_graph(X_scaled, k_neighbors=8):
    if X_scaled.shape[0] <= 1:
        return torch.tensor([[0], [0]], dtype=torch.long)
    k = min(k_neighbors, max(1, X_scaled.shape[0] - 1))
    knn_graph = kneighbors_graph(X_scaled, n_neighbors=k, mode='connectivity', include_self=False)
    return torch.tensor(np.vstack(knn_graph.nonzero()), dtype=torch.long)


def run_gat_inference(case_id, model_path=None, k_neighbors=8, threshold=0.5, device=None, top_n=50):
    """
    Run GAT inference for a case and return summary + high-score anomalies.
    """
    device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_path = model_path or os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'dl_models',
        'gat_best.pth'
    )

    df = extract_features(case_id)
    X_scaled, _scaler, df = preprocess_dataframe(df)

    if df is None or df.empty or X_scaled is None:
        return {
            "success": False,
            "case_id": case_id,
            "error": "No features available for inference",
        }

    # Load model (infer input/output sizes from checkpoint when possible)
    state_dict = torch.load(model_path, map_location=device)
    in_channels = len(FEATURE_COLUMNS)
    out_channels = 2
    try:
        if "g1.lin.weight" in state_dict:
            in_channels = int(state_dict["g1.lin.weight"].shape[1])
        if "g2.lin.weight" in state_dict:
            out_channels = int(state_dict["g2.lin.weight"].shape[0])
    except Exception:
        pass

    # Align feature matrix to expected input size
    if X_scaled.shape[1] != in_channels:
        if X_scaled.shape[1] < in_channels:
            pad = in_channels - X_scaled.shape[1]
            X_scaled = np.pad(X_scaled, ((0, 0), (0, pad)), mode="constant")
        else:
            X_scaled = X_scaled[:, :in_channels]

    # Build graph after feature alignment
    edge_index = _build_knn_graph(X_scaled, k_neighbors=k_neighbors)
    X_tensor = torch.tensor(X_scaled, dtype=torch.float32)
    data = Data(x=X_tensor, edge_index=edge_index).to(device)

    model = GAT(in_channels, 16, out_channels).to(device)
    model.load_state_dict(state_dict, strict=True)
    model.eval()

    with torch.no_grad():
        out = model(data.x, data.edge_index)
        probs = F.softmax(out, dim=1)
        probs_np = probs.detach().cpu().numpy()
        if out_channels == 2:
            anomaly_scores = probs_np[:, 1]
            predicted_class = np.argmax(probs_np, axis=1)
        else:
            # Use max probability excluding class 0 as anomaly score
            anomaly_scores = probs_np[:, 1:].max(axis=1)
            predicted_class = np.argmax(probs_np, axis=1)

    # Build output
    df = df.copy()
    df["Anomaly_Score"] = anomaly_scores
    df["Predicted_Class"] = predicted_class
    if out_channels == 2:
        df["Predicted_Label"] = np.where(df["Anomaly_Score"] >= threshold, "Anomaly", "Normal")
    else:
        df["Predicted_Label"] = np.where(df["Predicted_Class"] == 0, "Normal", "Anomaly")
    df["Predicted_Anomaly"] = (df["Anomaly_Score"] >= threshold).astype(int)
    df["Activity_Name"] = df["Activity_Type"].apply(lambda x: ACTIVITY_NAME.get(int(x), "Unknown"))
    df["Action_Name"] = df["Action"].apply(lambda x: ACTION_NAME.get(int(x), "Unknown"))

    top = df.sort_values("Anomaly_Score", ascending=False).head(top_n)

    top_records = []
    for _, row in top.iterrows():
        feature_snapshot = {col: float(row.get(col, 0)) for col in FEATURE_COLUMNS}
        class_name = (
            "Normal" if int(row.get("Predicted_Class", 0)) == 0 else f"Class {int(row.get('Predicted_Class', 0))}"
        )
        top_records.append({
            "activity_type": int(row.get("Activity_Type", 0)),
            "activity_name": row.get("Activity_Name"),
            "action": int(row.get("Action", 0)),
            "action_name": row.get("Action_Name"),
            "hour": float(row.get("Hour", 0)),
            "day_of_week": int(row.get("DayOfWeek", 0)),
            "is_weekend": int(row.get("IsWeekend", 0)),
            "file_size": float(row.get("File_Size", 0)),
            "is_private_ip": int(row.get("IsPrivateIP", 0)),
            "user_id": int(row.get("User_ID", 0)),
            "resource_accessed": int(row.get("Resource_Accessed", 0)),
            "login_attempts": int(row.get("Login_Attempts", 0)),
            "predicted_class": int(row.get("Predicted_Class", 0)),
            "class_name": class_name,
            "features": feature_snapshot,
            "anomaly_score": float(row.get("Anomaly_Score", 0)),
            "label": row.get("Predicted_Label"),
        })

    return {
        "success": True,
        "case_id": case_id,
        "total_activities": int(len(df)),
        "anomalies_detected": int((df["Predicted_Anomaly"] == 1).sum()),
        "threshold": float(threshold),
        "top_anomalies": top_records,
    }
