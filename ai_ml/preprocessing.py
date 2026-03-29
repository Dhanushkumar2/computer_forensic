"""
Preprocessing utilities for ML anomaly detection.
Extracts features from MongoDB, ensures required columns, and scales data.
"""

import numpy as np
from sklearn.preprocessing import StandardScaler

# Feature columns used in training (from notebook)
FEATURE_COLUMNS = [
    'User_ID', 'Activity_Type', 'Resource_Accessed', 'Action',
    'Login_Attempts', 'File_Size', 'Hour', 'File_Info_Missing',
    'Login_Info_Missing', 'Action_Missing', 'Anomaly_Missing',
    'DayOfWeek', 'IsWeekend', 'IP1', 'IP2', 'IP3', 'IP4',
    'IsPrivateIP', 'File_Size_Log', 'Anomaly_Label'
]


def extract_features(case_id):
    """Extract ML features for a case using the feature extractor."""
    from ai_ml.feature_extractor import ForensicFeatureExtractor

    extractor = ForensicFeatureExtractor()
    try:
        df = extractor.extract_features_from_case(case_id)
    finally:
        extractor.close()
    return df


def preprocess_dataframe(df, scaler=None):
    """
    Ensure required columns and scale features.

    Returns:
        X_scaled (np.ndarray), scaler (StandardScaler), df (DataFrame)
    """
    if df is None or df.empty:
        return None, None, df

    # Ensure all required columns exist
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = 0

    # Select and convert
    X = df[FEATURE_COLUMNS].to_numpy(dtype=np.float32)

    # Scale
    scaler = scaler or StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, scaler, df
