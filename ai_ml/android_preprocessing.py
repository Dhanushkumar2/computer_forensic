"""
Preprocessing for Android ML inference (TabTransformer).
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


def load_android_features(csv_path):
    """Load Android features CSV (same schema as fyp-phase2 dataset)."""
    df = pd.read_csv(csv_path, sep=';', engine='python')
    return df


def preprocess_android_df(df, selected_features):
    """
    Prepare numeric features for inference using selected feature list.

    Returns:
        X_scaled (np.ndarray), scaler (StandardScaler), df (DataFrame)
    """
    if df is None or df.empty:
        return None, None, df

    # Keep only numerical columns like in notebook
    numerical_cols = df.select_dtypes(include=["int64", "float64"]).columns
    X = df[numerical_cols].copy()

    # Replace inf and NaN
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.dropna(axis=1, how='all')
    X = X.fillna(X.median(numeric_only=True))

    # Remove constant columns
    variance = X.var()
    X = X.loc[:, variance > 0]

    # Ensure selected features exist
    for col in selected_features:
        if col not in X.columns:
            X[col] = 0

    # Select in correct order
    X = X[selected_features]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X.values.astype(np.float32))

    return X_scaled, scaler, df
