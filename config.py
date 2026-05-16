# config.py
import os

class Config:
    # API Configuration
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    
    # Redis Configuration (optional - for production)
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_DB = 0
    
    # Data paths
    CAB_RIDES_PATH = "D:\Glowlogics\dynamic price System\cab_rides.csv"
    WEATHER_PATH = "D:\Glowlogics\dynamic price System\weather.csv"
    
    
    # Model paths
    PRICE_MODEL_PATH = "models/price_predictor.pkl"
    XGBOOST_MODEL_PATH = "models/xgboost_model.json"
    SURGE_MODEL_PATH = "models/surge_predictor.pkl"
    
    # Ride-sharing specific config
    BASE_FARE = 5.0
    PER_MILE_RATE = 1.5
    PER_MINUTE_RATE = 0.5
    
    # Surge pricing thresholds
    SURGE_THRESHOLD_LOW = 1.2
    SURGE_THRESHOLD_MEDIUM = 1.5
    SURGE_THRESHOLD_HIGH = 2.0
    
    # Weather impact multipliers
    RAIN_MULTIPLIER = 1.3
    HIGH_TEMP_THRESHOLD = 30
    LOW_TEMP_THRESHOLD = 5
    
    # Time-based multipliers
    RUSH_HOUR_MULTIPLIER = 1.4
    LATE_NIGHT_MULTIPLIER = 1.3
    WEEKEND_MULTIPLIER = 1.15
    
    # Ride type base multipliers
    RIDE_TYPE_MULTIPLIERS = {
        "Lyft": 1.0,
        "Lyft XL": 1.5,
        "Lux": 2.0,
        "Lux Black": 2.5,
        "Shared": 0.7,
        "UberX": 1.0,
        "UberXL": 1.5,
        "Black": 2.0,
        "Black SUV": 2.5,
        "Taxi": 1.1
    }
    
    # ML Model parameters
    XGB_PARAMS = {
        'n_estimators': 100,  # Reduced for faster training
        'max_depth': 6,
        'learning_rate': 0.1,
        'random_state': 42
    }
    
    # Performance targets
    TARGET_MAE = 2.0
    TARGET_LATENCY_MS = 500