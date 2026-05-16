# load_my_data.py - Simple data loader for CSV files in current folder
import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

print("="*60)
print("RIDE PRICING DATA LOADER")
print("="*60)

# STEP 1: Get current folder (where your CSV files are)
current_folder = os.getcwd()
print(f"\n[INFO] Looking for CSV files in: {current_folder}")

# STEP 2: Check for CSV files in current folder
files_in_folder = os.listdir(current_folder)
csv_files = [f for f in files_in_folder if f.endswith('.csv')]
print(f"\n[INFO] CSV files found: {csv_files}")

# STEP 3: Find cab_rides.csv
cab_file = None
possible_cab_names = ['cab_rides.csv', 'cab_rides', 'cab.csv', 'rides.csv', 'cab_data.csv']

for name in possible_cab_names:
    if os.path.exists(name):
        cab_file = name
        break

# Also check for any file containing 'cab' or 'ride' in name
if cab_file is None:
    for file in csv_files:
        if 'cab' in file.lower() or 'ride' in file.lower():
            cab_file = file
            break

# STEP 4: Find weather.csv
weather_file = None
possible_weather_names = ['weather.csv', 'weather', 'weather_data.csv', 'weather_info.csv']

for name in possible_weather_names:
    if os.path.exists(name):
        weather_file = name
        break

# Also check for any file containing 'weather' in name
if weather_file is None:
    for file in csv_files:
        if 'weather' in file.lower():
            weather_file = file
            break

# STEP 5: If files not found, ask user
if cab_file is None:
    print("\n[WARNING] Could not find cab_rides.csv automatically")
    print("Please type the exact filename (e.g., cab_rides.csv):")
    cab_file = input().strip()

if weather_file is None:
    print("\n[WARNING] Could not find weather.csv automatically")
    print("Please type the exact filename (e.g., weather.csv):")
    weather_file = input().strip()

# STEP 6: Load the data
print("\n" + "="*60)
print("LOADING DATA")
print("="*60)

try:
    # Load cab rides
    print(f"\n[INFO] Loading {cab_file}...")
    cab_df = pd.read_csv(cab_file)
    print(f"[SUCCESS] Loaded {len(cab_df)} rows")
    print(f"   Columns: {', '.join(cab_df.columns[:8])}...")
    
    # Load weather
    print(f"\n[INFO] Loading {weather_file}...")
    weather_df = pd.read_csv(weather_file)
    print(f"[SUCCESS] Loaded {len(weather_df)} rows")
    print(f"   Columns: {', '.join(weather_df.columns[:8])}...")
    
except FileNotFoundError as e:
    print(f"\n[ERROR] {e}")
    print("\n[SOLUTION] Make sure your CSV files are in this folder:")
    print(f"   {current_folder}")
    exit(1)
except Exception as e:
    print(f"\n[ERROR] Could not read file: {e}")
    exit(1)

# STEP 7: Display sample data
print("\n" + "="*60)
print("DATA PREVIEW")
print("="*60)

print("\n[CAB RIDES DATA] (first 3 rows):")
print(cab_df.head(3))

print("\n[WEATHER DATA] (first 3 rows):")
print(weather_df.head(3))

# STEP 8: Data info
print("\n" + "="*60)
print("DATA INFORMATION")
print("="*60)

print(f"\n[CAB] Columns: {cab_df.columns.tolist()}")
print(f"[WEATHER] Columns: {weather_df.columns.tolist()}")

# STEP 9: Process timestamps
print("\n" + "="*60)
print("PROCESSING TIMESTAMPS")
print("="*60)

# Handle cab timestamps
if 'time_stamp' in cab_df.columns:
    cab_df['datetime'] = pd.to_datetime(cab_df['time_stamp'], unit='ms')
    print("[SUCCESS] Converted cab timestamps (milliseconds)")
elif 'timestamp' in cab_df.columns:
    cab_df['datetime'] = pd.to_datetime(cab_df['timestamp'])
    print("[SUCCESS] Converted cab timestamps")
else:
    print("[WARNING] No timestamp column found in cab data")
    cab_df['datetime'] = pd.Timestamp.now()

# Handle weather timestamps
if 'time_stamp' in weather_df.columns:
    weather_df['datetime'] = pd.to_datetime(weather_df['time_stamp'], unit='s')
    print("[SUCCESS] Converted weather timestamps (seconds)")
elif 'timestamp' in weather_df.columns:
    weather_df['datetime'] = pd.to_datetime(weather_df['timestamp'])
    print("[SUCCESS] Converted weather timestamps")
elif 'Time' in weather_df.columns:
    weather_df['datetime'] = pd.to_datetime(weather_df['Time'])
    print("[SUCCESS] Converted weather timestamps (Time column)")
else:
    print("[WARNING] No timestamp column found in weather data")
    weather_df['datetime'] = pd.Timestamp.now()

# STEP 10: Simple merge (by hour)
print("\n" + "="*60)
print("MERGING DATASETS")
print("="*60)

# Extract hour from datetime
cab_df['hour'] = cab_df['datetime'].dt.hour
cab_df['day'] = cab_df['datetime'].dt.dayofweek
cab_df['month'] = cab_df['datetime'].dt.month

if 'datetime' in weather_df.columns:
    weather_df['hour'] = weather_df['datetime'].dt.hour
    
    # Calculate average weather by hour
    weather_columns = []
    for col in ['temp', 'temperature', 'rain', 'humidity', 'wind', 'pressure', 'clouds']:
        if col in weather_df.columns:
            weather_columns.append(col)
    
    if weather_columns:
        weather_by_hour = weather_df.groupby('hour')[weather_columns].mean().reset_index()
        print(f"[INFO] Averaging weather by hour: {weather_columns}")
    else:
        # Create dummy weather data if no weather columns found
        weather_by_hour = pd.DataFrame({'hour': range(24)})
        for col in ['temp', 'rain', 'humidity', 'wind']:
            weather_by_hour[col] = 20 if col == 'temp' else 0 if col == 'rain' else 0.5
        print("[WARNING] No weather columns found - using default values")
    
    # Merge cab data with weather by hour
    merged_df = cab_df.merge(weather_by_hour, on='hour', how='left')
    print("[SUCCESS] Merged by hour (weather averaged by hour)")
else:
    merged_df = cab_df.copy()
    print("[WARNING] Could not merge - using cab data only")

# STEP 11: Add derived features
print("\n" + "="*60)
print("ADDING FEATURES")
print("="*60)

# Time features
merged_df['is_weekend'] = (merged_df['day'] >= 5).astype(int)
merged_df['is_rush_hour'] = ((merged_df['hour'] >= 7) & (merged_df['hour'] <= 9) | 
                              (merged_df['hour'] >= 17) & (merged_df['hour'] <= 19)).astype(int)
merged_df['is_late_night'] = ((merged_df['hour'] >= 22) | (merged_df['hour'] <= 5)).astype(int)

# Cyclical features
merged_df['hour_sin'] = np.sin(2 * np.pi * merged_df['hour'] / 24)
merged_df['hour_cos'] = np.cos(2 * np.pi * merged_df['hour'] / 24)

# Price per mile
merged_df['price_per_mile'] = merged_df['price'] / merged_df['distance'].replace(0, 0.1)

print("[SUCCESS] Added time features")
print("[SUCCESS] Added price per mile")

# STEP 12: Fill missing weather data
weather_cols = ['temp', 'rain', 'humidity', 'wind', 'pressure', 'clouds']
for col in weather_cols:
    if col in merged_df.columns:
        merged_df[col] = merged_df[col].fillna(merged_df[col].median())
    else:
        merged_df[col] = 20 if col == 'temp' else 0 if col == 'rain' else 0.5

print("[SUCCESS] Filled missing weather data")

# STEP 13: Handle missing surge multiplier
if 'surge_multiplier' in merged_df.columns:
    merged_df['surge_multiplier'] = merged_df['surge_multiplier'].fillna(1.0)
else:
    merged_df['surge_multiplier'] = 1.0

# STEP 14: Remove outliers
original_count = len(merged_df)
merged_df = merged_df[merged_df['price'] < merged_df['price'].quantile(0.99)]
merged_df = merged_df[merged_df['distance'] < merged_df['distance'].quantile(0.99)]
merged_df = merged_df[merged_df['distance'] > 0]
print(f"[SUCCESS] Removed outliers: {original_count} -> {len(merged_df)} rows")

# STEP 15: Save merged data
output_file = 'merged_ride_data.csv'
merged_df.to_csv(output_file, index=False)
print(f"\n[SUCCESS] Saved merged data to: {output_file}")

# STEP 16: Show summary
print("\n" + "="*60)
print("FINAL SUMMARY")
print("="*60)

print(f"\n[DATASET] Size: {len(merged_df)} rows, {len(merged_df.columns)} columns")
print(f"\n[PRICE STATISTICS]")
print(f"   Min: ${merged_df['price'].min():.2f}")
print(f"   Max: ${merged_df['price'].max():.2f}")
print(f"   Avg: ${merged_df['price'].mean():.2f}")
print(f"   Median: ${merged_df['price'].median():.2f}")

print(f"\n[DISTANCE STATISTICS]")
print(f"   Min: {merged_df['distance'].min():.2f} miles")
print(f"   Max: {merged_df['distance'].max():.2f} miles")
print(f"   Avg: {merged_df['distance'].mean():.2f} miles")

print(f"\n[RIDE TYPES] (top 5):")
for ride_type in merged_df['name'].value_counts().head(5).items():
    print(f"   {ride_type[0]}: {ride_type[1]} rides")

print(f"\n[TOP DESTINATIONS] (top 5):")
for dest in merged_df['destination'].value_counts().head(5).items():
    print(f"   {dest[0]}: {dest[1]} rides")

# STEP 17: Prepare for ML training
print("\n" + "="*60)
print("PREPARING FOR MODEL TRAINING")
print("="*60)

# Create feature columns for training
feature_cols = ['distance', 'hour', 'day', 'month', 'is_weekend', 'is_rush_hour', 
                'is_late_night', 'hour_sin', 'hour_cos', 'price_per_mile']

# Add weather columns if they exist
for col in ['temp', 'rain', 'humidity', 'wind']:
    if col in merged_df.columns:
        feature_cols.append(col)

# Save feature columns
try:
    import joblib
    feature_file = 'feature_columns.pkl'
    joblib.dump(feature_cols, feature_file)
    print(f"[SUCCESS] Saved feature columns: {feature_cols[:8]}...")
    
    # Save target column info
    target_info = {'target': 'price', 'description': 'Ride price in dollars'}
    joblib.dump(target_info, 'target_info.pkl')
    print("[SUCCESS] Saved target info")
except Exception as e:
    print(f"[WARNING] Could not save feature columns: {e}")

print("\n" + "="*60)
print("DATA LOADING COMPLETE!")
print("="*60)

print("\n[OUTPUT FILES CREATED]:")
print(f"   1. {output_file} - Merged dataset for analysis")
print(f"   2. feature_columns.pkl - List of features for ML")
print(f"   3. target_info.pkl - Target variable info")

print("\n[NEXT STEPS]:")
print("   Step 1: Train your model")
print("   python train_model.py")
print("")
print("   Step 2: Run the API server")
print("   uvicorn main:app --reload")
print("")
print("   Step 3: Launch the dashboard")
print("   streamlit run dashboard.py")

print("\n" + "="*60)