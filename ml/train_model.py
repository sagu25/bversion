"""
Train anomaly detection ensemble on realistic OT/SCADA grid data.
IsolationForest (unsupervised) + RandomForestClassifier (supervised).
Run from aegis-poc/ root: python ml/train_model.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import joblib
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from generate_grid_data import build_dataset, FEATURES, LABEL_NAMES

def train():
    print("Generating training data...")
    df = build_dataset(n_normal=3000, n_each_attack=800)
    print(f"Dataset: {len(df)} samples")
    print(df['label_name'].value_counts().to_string()); print()

    X = df[FEATURES].values.astype(float)
    y = df['label'].values

    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Isolation Forest — trained on normal sessions only (unsupervised)
    X_normal = X_scaled[y == 0]
    iso = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
    iso.fit(X_normal)
    print("Isolation Forest trained on normal data.")

    # Random Forest — supervised multi-class classifier
    X_tr, X_te, y_tr, y_te = train_test_split(X_scaled, y, test_size=0.2, random_state=42, stratify=y)
    rf = RandomForestClassifier(n_estimators=200, random_state=42, class_weight='balanced')
    rf.fit(X_tr, y_tr)
    print("\nRandom Forest report:")
    print(classification_report(y_te, rf.predict(X_te), target_names=[LABEL_NAMES[i] for i in range(5)]))

    os.makedirs('ml', exist_ok=True)
    bundle = {'scaler': scaler, 'iso_forest': iso, 'rf_classifier': rf,
              'features': FEATURES, 'attack_names': LABEL_NAMES}
    joblib.dump(bundle, 'ml/model.pkl')
    print("Model saved → ml/model.pkl")

if __name__ == '__main__':
    train()
