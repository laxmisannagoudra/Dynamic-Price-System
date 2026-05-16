import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set UTF-8 encoding for Windows console
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Set style for better visualizations
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

print("="*80)
print("UBER/LYFT RIDES & WEATHER DATA ANALYSIS")
print("="*80)

# ============================================
# STEP 1: LOAD DATA
# ============================================
print("\n[1] Loading data files...")

# Load weather data
weather_df = pd.read_csv('weather.csv')
print(f"[OK] Weather data: {len(weather_df):,} records")

# Load cab rides data
rides_df = pd.read_csv('cab_rides.csv')
print(f"[OK] Cab rides data: {len(rides_df):,} records")

# Display column names to see what we have
print("\nColumns in rides data:")
print(rides_df.columns.tolist())

print("\nFirst 5 rows of rides data:")
print(rides_df.head())

# ============================================
# STEP 2: DATA CLEANING & PREPARATION
# ============================================
print("\n" + "="*80)
print("DATA CLEANING & PREPARATION")
print("="*80)

# Check available columns and rename if necessary
# Your data has columns: distance, cab_type, time_stamp, destination, source, price, surge_multiplier, id, product_id, name

# Create a unique ID for each ride if not present
if 'id' in rides_df.columns:
    rides_df['ride_id'] = rides_df['id']
elif 'ride_id' not in rides_df.columns:
    rides_df['ride_id'] = range(len(rides_df))

# Clean rides data
# Handle timestamp - check if it's in seconds or milliseconds
rides_df['time_stamp'] = pd.to_numeric(rides_df['time_stamp'], errors='coerce')

# Check timestamp range to determine if it's seconds or milliseconds
sample_timestamp = rides_df['time_stamp'].iloc[0] if len(rides_df) > 0 else 0
print(f"\nSample timestamp value: {sample_timestamp}")

# Convert timestamp to datetime
# If timestamp > 10^12, it's likely in milliseconds
if sample_timestamp > 10**12:
    print("Detected timestamps in milliseconds, converting to seconds...")
    rides_df['datetime'] = pd.to_datetime(rides_df['time_stamp'] / 1000, unit='s', errors='coerce')
else:
    print("Detected timestamps in seconds...")
    rides_df['datetime'] = pd.to_datetime(rides_df['time_stamp'], unit='s', errors='coerce')

# Handle missing prices
rides_df['price'] = pd.to_numeric(rides_df['price'], errors='coerce')
if rides_df['price'].isna().any():
    print(f"Filling {rides_df['price'].isna().sum()} missing prices with median value")
    rides_df['price'].fillna(rides_df['price'].median(), inplace=True)

# Ensure surge_multiplier is numeric
rides_df['surge_multiplier'] = pd.to_numeric(rides_df['surge_multiplier'], errors='coerce').fillna(1)

# Extract location info (source and destination)
rides_df['source'] = rides_df['source'].fillna('Unknown')
rides_df['destination'] = rides_df['destination'].fillna('Unknown')

# Extract cab type
print(f"\nCab types in data: {rides_df['cab_type'].unique()}")

# Distance analysis
rides_df['distance'] = pd.to_numeric(rides_df['distance'], errors='coerce')
print(f"Distance range: {rides_df['distance'].min():.2f} to {rides_df['distance'].max():.2f} miles")

# Clean weather data - timestamps are in seconds
weather_df['time_stamp'] = pd.to_numeric(weather_df['time_stamp'], errors='coerce')
weather_df = weather_df.dropna(subset=['time_stamp'])
weather_df['datetime'] = pd.to_datetime(weather_df['time_stamp'], unit='s', errors='coerce')
weather_df['rain'] = pd.to_numeric(weather_df['rain'], errors='coerce').fillna(0)
weather_df['temp'] = pd.to_numeric(weather_df['temp'], errors='coerce')
weather_df['humidity'] = pd.to_numeric(weather_df['humidity'], errors='coerce')
weather_df['wind'] = pd.to_numeric(weather_df['wind'], errors='coerce')

# Remove any rows with invalid datetime
rides_df = rides_df.dropna(subset=['datetime'])
weather_df = weather_df.dropna(subset=['datetime'])

print(f"\nValid rides after timestamp conversion: {len(rides_df):,}")
print(f"Valid weather records after timestamp conversion: {len(weather_df):,}")

# Extract time features for both datasets
for df in [rides_df, weather_df]:
    df['hour'] = df['datetime'].dt.hour
    df['day'] = df['datetime'].dt.day
    df['month'] = df['datetime'].dt.month
    df['day_of_week'] = df['datetime'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

if len(rides_df) > 0 and len(weather_df) > 0:
    print(f"\nDate range in rides: {rides_df['datetime'].min()} to {rides_df['datetime'].max()}")
    print(f"Date range in weather: {weather_df['datetime'].min()} to {weather_df['datetime'].max()}")
else:
    print("\nERROR: No valid dates found in one of the datasets!")
    print("Please check your timestamp columns.")
    sys.exit(1)

# ============================================
# STEP 3: MERGE RIDES WITH WEATHER DATA
# ============================================
print("\n" + "="*80)
print("MERGING RIDES WITH WEATHER DATA")
print("="*80)

# Round timestamps to nearest hour for better matching
rides_df['timestamp_hour'] = rides_df['datetime'].dt.floor('H')
weather_df['timestamp_hour'] = weather_df['datetime'].dt.floor('H')

# Merge on hour and location
merged_df = rides_df.merge(
    weather_df[['timestamp_hour', 'location', 'temp', 'rain', 'humidity', 'wind', 'pressure', 'clouds']],
    left_on=['timestamp_hour', 'source'],
    right_on=['timestamp_hour', 'location'],
    how='left'
)

# Rename weather columns to avoid confusion
merged_df = merged_df.rename(columns={
    'temp': 'weather_temp',
    'rain': 'weather_rain',
    'humidity': 'weather_humidity',
    'wind': 'weather_wind',
    'pressure': 'weather_pressure',
    'clouds': 'weather_clouds'
})

# Drop the extra location column
if 'location' in merged_df.columns:
    merged_df = merged_df.drop('location', axis=1)

# Drop the temporary hour column
if 'timestamp_hour' in merged_df.columns:
    merged_df = merged_df.drop('timestamp_hour', axis=1)

print(f"[OK] Merged data: {len(merged_df):,} rides with weather data")
print(f"   Rides with weather match: {merged_df['weather_temp'].notna().sum():,}/{len(merged_df):,}")

# Remove rows without weather data
merged_df = merged_df.dropna(subset=['weather_temp'])
print(f"   After cleaning: {len(merged_df):,} rides")

if len(merged_df) == 0:
    print("\nERROR: No matches found between rides and weather data!")
    print("Please check that location names match between both files.")
    print("\nLocations in rides data:")
    print(rides_df['source'].unique())
    print("\nLocations in weather data:")
    print(weather_df['location'].unique())
    sys.exit(1)

# ============================================
# STEP 4: EXPLORATORY DATA ANALYSIS
# ============================================
print("\n" + "="*80)
print("EXPLORATORY DATA ANALYSIS")
print("="*80)

# Ride statistics by cab type
print("\nRide Statistics by Cab Type:")
cab_stats = rides_df.groupby('cab_type').agg({
    'ride_id': 'count',
    'price': 'mean',
    'distance': 'mean',
    'surge_multiplier': 'mean'
}).round(2)
cab_stats.columns = ['Total Rides', 'Avg Price ($)', 'Avg Distance (miles)', 'Avg Surge']
print(cab_stats)

# Most popular routes
print("\nMost Popular Routes:")
popular_routes = rides_df.groupby(['source', 'destination']).size().sort_values(ascending=False).head(10)
for (source, dest), count in popular_routes.items():
    print(f"   {source} -> {dest}: {count:,} rides")

# Most popular locations
print("\nMost Popular Pickup Locations:")
popular_pickups = rides_df['source'].value_counts().head(10)
for location, count in popular_pickups.items():
    print(f"   {location}: {count:,} rides")

# Weather statistics during rides
print("\nWeather Statistics During Rides:")
print(f"   Temperature: {merged_df['weather_temp'].min():.1f}F to {merged_df['weather_temp'].max():.1f}F (Avg: {merged_df['weather_temp'].mean():.1f}F)")
print(f"   Humidity: {merged_df['weather_humidity'].min():.1f}% to {merged_df['weather_humidity'].max():.1f}% (Avg: {merged_df['weather_humidity'].mean():.1f}%)")
print(f"   Wind Speed: {merged_df['weather_wind'].min():.1f} to {merged_df['weather_wind'].max():.1f} (Avg: {merged_df['weather_wind'].mean():.1f})")
print(f"   Rainy rides: {(merged_df['weather_rain'] > 0).sum():,} ({((merged_df['weather_rain'] > 0).mean())*100:.1f}%)")

# ============================================
# STEP 5: WEATHER IMPACT ON RIDE VOLUME & PRICING
# ============================================
print("\n" + "="*80)
print("WEATHER IMPACT ON RIDES")
print("="*80)

# Separate rainy vs dry rides
rainy_rides = merged_df[merged_df['weather_rain'] > 0]
dry_rides = merged_df[merged_df['weather_rain'] == 0]

if len(rainy_rides) > 0 and len(dry_rides) > 0:
    print(f"\nRide Volume Comparison:")
    print(f"   Rainy conditions: {len(rainy_rides):,} rides ({len(rainy_rides)/len(merged_df)*100:.1f}%)")
    print(f"   Dry conditions: {len(dry_rides):,} rides ({len(dry_rides)/len(merged_df)*100:.1f}%)")
    
    # Price comparison
    print(f"\nPrice Comparison:")
    print(f"   Rainy conditions - Avg Price: ${rainy_rides['price'].mean():.2f}")
    print(f"   Dry conditions - Avg Price: ${dry_rides['price'].mean():.2f}")
    if dry_rides['price'].mean() > 0:
        print(f"   Difference: ${rainy_rides['price'].mean() - dry_rides['price'].mean():.2f} ({(rainy_rides['price'].mean()/dry_rides['price'].mean() - 1)*100:.1f}% higher in rain)")
    
    # Surge multiplier comparison
    print(f"\nSurge Multiplier Comparison:")
    print(f"   Rainy conditions: {rainy_rides['surge_multiplier'].mean():.2f}x")
    print(f"   Dry conditions: {dry_rides['surge_multiplier'].mean():.2f}x")
    if dry_rides['surge_multiplier'].mean() > 0:
        print(f"   Difference: {(rainy_rides['surge_multiplier'].mean() - dry_rides['surge_multiplier'].mean())*100:.0f}% higher in rain")
    
    # By cab type
    print(f"\nPrice Impact by Cab Type (Rainy vs Dry):")
    cab_weather_impact = merged_df.groupby(['cab_type', merged_df['weather_rain'] > 0])['price'].mean().unstack()
    if cab_weather_impact.shape[1] == 2:
        cab_weather_impact.columns = ['Dry_Price', 'Rainy_Price']
        cab_weather_impact['Difference'] = cab_weather_impact['Rainy_Price'] - cab_weather_impact['Dry_Price']
        cab_weather_impact['Percent_Increase'] = (cab_weather_impact['Rainy_Price'] / cab_weather_impact['Dry_Price'] - 1) * 100
        print(cab_weather_impact.round(2))
else:
    print("\nNot enough data for rainy vs dry comparison")

# ============================================
# STEP 6: TEMPERATURE IMPACT ANALYSIS
# ============================================
print("\n" + "="*80)
print("TEMPERATURE IMPACT ANALYSIS")
print("="*80)

# Create temperature bins
temp_bins = [0, 32, 50, 70, 85, 100]
temp_labels = ['<32F (Freezing)', '32-50F (Cold)', '50-70F (Mild)', '70-85F (Warm)', '>85F (Hot)']
merged_df['temp_category'] = pd.cut(merged_df['weather_temp'], bins=temp_bins, labels=temp_labels)

# Analyze by temperature
temp_analysis = merged_df.groupby('temp_category').agg({
    'price': 'mean',
    'surge_multiplier': 'mean',
    'ride_id': 'count'
}).round(2)
temp_analysis.columns = ['Avg Price ($)', 'Avg Surge', 'Number of Rides']
print("\nRide Metrics by Temperature:")
print(temp_analysis)

# ============================================
# STEP 7: TIME-BASED ANALYSIS
# ============================================
print("\n" + "="*80)
print("TIME-BASED ANALYSIS")
print("="*80)

# Rides by hour
rides_by_hour = rides_df.groupby('hour').size()
print(f"\nPeak Hours (by ride volume):")
peak_hours = rides_by_hour.nlargest(5)
for hour, count in peak_hours.items():
    if not pd.isna(hour):
        print(f"   {int(hour)}:00 - {count:,} rides")

# Price by hour
price_by_hour = rides_df.groupby('hour')['price'].mean()
print(f"\nMost Expensive Hours (by average price):")
expensive_hours = price_by_hour.nlargest(3)
for hour, price in expensive_hours.items():
    if not pd.isna(hour):
        print(f"   {int(hour)}:00 - ${price:.2f}")

# Price by day of week
day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
price_by_dow = rides_df.groupby('day_of_week')['price'].mean()
print(f"\nAverage Price by Day of Week:")
for i, price in price_by_dow.items():
    if i < len(day_names):
        print(f"   {day_names[i]}: ${price:.2f}")

# ============================================
# STEP 8: CORRELATION ANALYSIS
# ============================================
print("\n" + "="*80)
print("CORRELATION ANALYSIS")
print("="*80)

# Calculate correlations
correlation_vars = ['weather_temp', 'weather_rain', 'weather_humidity', 'weather_wind', 
                    'distance', 'price', 'surge_multiplier', 'hour', 'is_weekend']
available_vars = [v for v in correlation_vars if v in merged_df.columns]

if len(available_vars) >= 2:
    correlation_matrix = merged_df[available_vars].corr()
    
    if 'price' in correlation_matrix.columns:
        print("\nCorrelation with Price:")
        price_corr = correlation_matrix['price'].sort_values(ascending=False)
        for var, corr in price_corr.items():
            if var != 'price' and not pd.isna(corr):
                print(f"   {var}: {corr:.3f}")
    
    if 'surge_multiplier' in correlation_matrix.columns:
        print("\nCorrelation with Surge Multiplier:")
        surge_corr = correlation_matrix['surge_multiplier'].sort_values(ascending=False)
        for var, corr in surge_corr.items():
            if var != 'surge_multiplier' and not pd.isna(corr):
                print(f"   {var}: {corr:.3f}")
else:
    print("Not enough variables for correlation analysis")

# ============================================
# STEP 9: CREATE VISUALIZATIONS
# ============================================
print("\n" + "="*80)
print("CREATING VISUALIZATIONS")
print("="*80)

try:
    # Create main dashboard
    fig = plt.figure(figsize=(20, 16))
    fig.suptitle('Uber/Lyft Rides vs Weather Analysis Dashboard', fontsize=18, fontweight='bold')
    
    # 1. Rides by Cab Type
    ax1 = plt.subplot(3, 3, 1)
    cab_counts = rides_df['cab_type'].value_counts()
    bars = ax1.bar(range(len(cab_counts)), cab_counts.values, color=['#ff6b6b', '#4ecdc4'][:len(cab_counts)], alpha=0.7)
    ax1.set_xticks(range(len(cab_counts)))
    ax1.set_xticklabels(cab_counts.index)
    ax1.set_title('Rides by Cab Type')
    ax1.set_ylabel('Number of Rides')
    for bar, val in zip(bars, cab_counts.values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(cab_counts.values)*0.01, 
                 f'{val:,}', ha='center', fontweight='bold')
    
    # 2. Price Distribution by Weather
    ax2 = plt.subplot(3, 3, 2)
    if len(dry_rides) > 0 and len(rainy_rides) > 0:
        ax2.hist(dry_rides['price'], bins=30, alpha=0.5, label='Dry', color='#95a5a6', edgecolor='black')
        ax2.hist(rainy_rides['price'], bins=30, alpha=0.5, label='Rainy', color='#3498db', edgecolor='black')
        ax2.legend()
    else:
        ax2.hist(rides_df['price'], bins=30, alpha=0.7, color='#95a5a6', edgecolor='black')
    ax2.set_xlabel('Price ($)')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Price Distribution')
    
    # 3. Temperature vs Price Scatter
    ax3 = plt.subplot(3, 3, 3)
    scatter = ax3.scatter(merged_df['weather_temp'], merged_df['price'], 
                          c=merged_df['weather_rain'], cmap='coolwarm', alpha=0.5, s=30)
    ax3.set_xlabel('Temperature (F)')
    ax3.set_ylabel('Price ($)')
    ax3.set_title('Temperature vs Ride Price')
    plt.colorbar(scatter, ax=ax3, label='Rain Amount')
    
    # 4. Average Price by Hour
    ax4 = plt.subplot(3, 3, 4)
    price_by_hour = rides_df.groupby('hour')['price'].mean()
    ax4.plot(price_by_hour.index, price_by_hour.values, marker='o', linewidth=2, markersize=8, color='#e74c3c')
    ax4.set_xlabel('Hour of Day')
    ax4.set_ylabel('Average Price ($)')
    ax4.set_title('Price Throughout the Day')
    ax4.set_xticks(range(0, 24, 4))
    ax4.grid(True, alpha=0.3)
    
    # 5. Surge Multiplier by Hour
    ax5 = plt.subplot(3, 3, 5)
    surge_by_hour = rides_df.groupby('hour')['surge_multiplier'].mean()
    ax5.plot(surge_by_hour.index, surge_by_hour.values, marker='o', linewidth=2, color='#27ae60')
    ax5.set_xlabel('Hour of Day')
    ax5.set_ylabel('Average Surge Multiplier')
    ax5.set_title('Surge Pricing by Hour')
    ax5.set_xticks(range(0, 24, 4))
    ax5.grid(True, alpha=0.3)
    
    # 6. Most Popular Pickup Locations
    ax6 = plt.subplot(3, 3, 6)
    top_locations = rides_df['source'].value_counts().head(8)
    ax6.barh(range(len(top_locations)), top_locations.values, color='#9b59b6', alpha=0.7)
    ax6.set_yticks(range(len(top_locations)))
    ax6.set_yticklabels(top_locations.index)
    ax6.set_xlabel('Number of Rides')
    ax6.set_title('Most Popular Pickup Locations')
    
    # 7. Distance vs Price
    ax7 = plt.subplot(3, 3, 7)
    scatter = ax7.scatter(merged_df['distance'], merged_df['price'], 
                          c=merged_df['surge_multiplier'], cmap='plasma', alpha=0.5, s=20)
    ax7.set_xlabel('Distance (miles)')
    ax7.set_ylabel('Price ($)')
    ax7.set_title('Distance vs Price (colored by Surge)')
    plt.colorbar(scatter, ax=ax7, label='Surge Multiplier')
    
    # 8. Price by Temperature Category
    ax8 = plt.subplot(3, 3, 8)
    temp_price = merged_df.groupby('temp_category')['price'].mean()
    temp_price = temp_price.dropna()
    if len(temp_price) > 0:
        ax8.bar(range(len(temp_price)), temp_price.values, color='#e67e22', alpha=0.7)
        ax8.set_xticks(range(len(temp_price)))
        ax8.set_xticklabels(temp_price.index, rotation=45, ha='right')
        ax8.set_ylabel('Average Price ($)')
        ax8.set_title('Price by Temperature Category')
    
    # 9. Ride Volume by Day of Week
    ax9 = plt.subplot(3, 3, 9)
    rides_by_dow = rides_df.groupby('day_of_week').size()
    ax9.bar(range(len(rides_by_dow)), rides_by_dow.values, color='#1abc9c', alpha=0.7)
    ax9.set_xlabel('Day of Week')
    ax9.set_ylabel('Number of Rides')
    ax9.set_title('Rides by Day of Week')
    ax9.set_xticks(range(len(rides_by_dow)))
    ax9.set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][:len(rides_by_dow)])
    
    plt.tight_layout()
    plt.savefig('uber_weather_dashboard.png', dpi=150, bbox_inches='tight')
    print("[OK] Saved: uber_weather_dashboard.png")
    plt.close()
    
except Exception as e:
    print(f"Warning: Could not create all visualizations: {e}")

# ============================================
# STEP 10: STATISTICAL TEST (if enough data)
# ============================================
if len(rainy_rides) > 0 and len(dry_rides) > 0:
    print("\n" + "="*80)
    print("STATISTICAL TEST")
    print("="*80)
    
    # T-test: Price on rainy vs dry days
    t_stat, p_value = stats.ttest_ind(
        rainy_rides['price'], 
        dry_rides['price']
    )
    print(f"\nPrice Difference: Rainy vs Dry")
    print(f"   T-statistic: {t_stat:.3f}")
    print(f"   P-value: {p_value:.4f}")
    if p_value < 0.05:
        print("   [SIGNIFICANT] Statistically significant difference (p < 0.05)")
    else:
        print("   [NOT SIGNIFICANT] No statistically significant difference")

# ============================================
# STEP 11: FINAL SUMMARY
# ============================================
print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)

# Calculate key metrics
price_increase_rain = 0
if len(rainy_rides) > 0 and len(dry_rides) > 0 and dry_rides['price'].mean() > 0:
    price_increase_rain = (rainy_rides['price'].mean() / dry_rides['price'].mean() - 1) * 100

print(f"""
Summary Statistics:
-------------------
Total Rides Analyzed: {len(rides_df):,}
Total Rides with Weather Data: {len(merged_df):,}

Cab Type Distribution:
- Uber: {rides_df[rides_df['cab_type']=='Uber'].shape[0]:,} rides
- Lyft: {rides_df[rides_df['cab_type']=='Lyft'].shape[0]:,} rides

Weather Impact:
- Rainy rides: {(merged_df['weather_rain'] > 0).sum():,} ({((merged_df['weather_rain'] > 0).mean())*100:.1f}%)
- Average temperature during rides: {merged_df['weather_temp'].mean():.1f}F
- Rain increases price by: {price_increase_rain:.1f}%

Most Popular Pickup Location: {rides_df['source'].mode().iloc[0] if len(rides_df) > 0 else 'N/A'}
Most Popular Route: {rides_df.groupby(['source', 'destination']).size().idxmax() if len(rides_df) > 0 else 'N/A'}

Files Generated:
1. uber_weather_dashboard.png - Main analysis dashboard
""")

print("\n[SUCCESS] Analysis completed successfully!")