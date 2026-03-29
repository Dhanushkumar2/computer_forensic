"""
Android TabTransformer inference pipeline.
Uses selected features from fyp-phase2 notebook and a finetuned model.
"""

import json
import os
import torch
import torch.nn as nn
import numpy as np
import torch.nn.functional as F

from ai_ml.android_preprocessing import load_android_features, preprocess_android_df


class TabTransformer(nn.Module):
    def __init__(self, input_dim, embed_dim=128, num_heads=8, num_layers=2, dropout=0.3):
        super().__init__()
        self.embedding = nn.Linear(input_dim, embed_dim)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dropout=dropout,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(embed_dim, 2)

    def forward(self, x):
        x = self.embedding(x)
        x = x.unsqueeze(1)
        x = self.transformer(x)
        x = x.squeeze(1)
        x = self.dropout(x)
        x = self.fc(x)
        return x


def _load_selected_features(features_path):
    with open(features_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("selected_features", [])


def run_android_inference(
    csv_path,
    features_path,
    model_path,
    threshold=0.5,
    top_n=50,
    device=None,
):
    """
    Run Android TabTransformer inference from a CSV.
    """
    device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")

    selected_features = _load_selected_features(features_path)
    if not selected_features:
        return {"success": False, "error": "Selected feature list is empty", "csv_path": csv_path}

    df = load_android_features(csv_path)
    X_scaled, _scaler, df = preprocess_android_df(df, selected_features)

    if X_scaled is None or df is None or df.empty:
        return {"success": False, "error": "No data available for inference", "csv_path": csv_path}

    X_tensor = torch.tensor(X_scaled, dtype=torch.float32).to(device)

    model = TabTransformer(input_dim=len(selected_features)).to(device)
    state_dict = torch.load(model_path, map_location=device)
    if "embedding.weight" in state_dict:
        expected_in = state_dict["embedding.weight"].shape[1]
        if expected_in != len(selected_features):
            return {
                "success": False,
                "error": f"Selected feature count ({len(selected_features)}) does not match model input ({expected_in}).",
                "csv_path": csv_path,
            }
    model.load_state_dict(state_dict)
    model.eval()

    with torch.no_grad():
        outputs = model(X_tensor)
        probs = F.softmax(outputs, dim=1)[:, 1].cpu().numpy()

    df = df.copy()
    df["Anomaly_Score"] = probs
    df["Predicted_Label"] = np.where(df["Anomaly_Score"] >= threshold, "malware", "benign")

    top = df.sort_values("Anomaly_Score", ascending=False).head(top_n)

    results = []
    for _, row in top.iterrows():
        results.append({
            "name": row.get("name"),
            "package_name": row.get("package_name"),
            "path": row.get("path"),
            "mtime": row.get("mtime"),
            "size": row.get("size"),
            "anomaly_score": float(row.get("Anomaly_Score", 0)),
            "label": row.get("Predicted_Label"),
        })

    return {
        "success": True,
        "total_samples": int(len(df)),
        "threshold": float(threshold),
        "top_anomalies": results,
    }
