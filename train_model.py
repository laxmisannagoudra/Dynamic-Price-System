# train_model.py - Train the price prediction model
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import warnings
warnings.filterwarnings('ignore')

print("="*60)
print("TRAINING PRICE PREDICTION MODEL")
print("="*60)

# Load the merged data
print("\n[1] Loading merged data...")
df = pd.read_csv('merged_ride_data.csv')
print(f"    Loaded {len(df)} rows, {len(df.columns)} columns")

# Load feature columns
try:
    feature_cols = joblib.load('feature_columns.pkl')
    print(f"    Using {len(feature_cols)} features")
except:
    # Define features manually if file not found
    feature_cols = ['distance', 'hour', 'day', 'month', 'is_weekend', 
                    'is_rush_hour', 'is_late_night', 'hour_sin', 'hour_cos', 
                    'price_per_mile', 'temp', 'rain', 'humidity', 'wind']
    print(f"    Using manual features: {len(feature_cols)}")

# Prepare features and target
print("\n[2] Preparing features...")
X = df[feature_cols]
y = df['price']

# Handle any missing values
X = X.fillna(X.mean())
print(f"    Feature matrix: {X.shape}")
print(f"    Target: {y.shape}")

# Split data
print("\n[3] Splitting data...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"    Training: {len(X_train)} rows")
print(f"    Testing: {len(X_test)} rows")

# Train model
print("\n[4] Training Random Forest model...")
model = RandomForestRegressor(
    n_estimators=100,
    max_depth=10,
    min_samples_split=5,
    random_state=42,
    n_jobs=-1
)
model.fit(X_train, y_train)

# Evaluate
print("\n[5] Evaluating model...")
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"\n" + "="*60)
print("MODEL PERFORMANCE")
print("="*60)
print(f"MAE (Mean Absolute Error): ${mae:.2f}")
print(f"R² Score: {r2:.4f}")
print("="*60)

# Save model
print("\n[6] Saving model...")
joblib.dump(model, 'price_model.pkl')
joblib.dump(feature_cols, 'model_features.pkl')
print("    Saved: price_model.pkl")
print("    Saved: model_features.pkl")

print("\n" + "="*60)
print("TRAINING COMPLETE!")
print("="*60)
print("\nNext step: Run the API server")
print("Command: uvicorn main:app --reload")