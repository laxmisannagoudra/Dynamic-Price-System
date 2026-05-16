# main.py - Fixed version without Unicode characters
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import pandas as pd
import numpy as np
import joblib
import uvicorn
import warnings
warnings.filterwarnings('ignore')

# Initialize FastAPI
app = FastAPI(title="Ride Pricing API", version="1.0")

# Enable CORS - Allow all origins for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model
print("="*50)
print("Starting Ride Pricing API...")
print("="*50)

model = None
feature_cols = None

try:
    model = joblib.load('price_model.pkl')
    feature_cols = joblib.load('model_features.pkl')
    print("[OK] Model loaded successfully")
    print(f"[OK] Features: {len(feature_cols)}")
except FileNotFoundError:
    print("[WARNING] Model not found. Run 'python train_model.py' first")
    print("[WARNING] Using fallback pricing mode")
except Exception as e:
    print(f"[WARNING] Error loading model: {e}")

# Request/Response models
class RideRequest(BaseModel):
    source: str
    destination: str
    distance: float
    ride_type: str = "Lyft"

class WeatherRequest(BaseModel):
    temp: float = 20
    rain: float = 0
    humidity: float = 0.5
    wind: float = 5

class PricingRequest(BaseModel):
    ride: RideRequest
    weather: WeatherRequest
    time_stamp: datetime = None

class PricingResponse(BaseModel):
    ride_type: str
    source: str
    destination: str
    distance: float
    base_fare: float
    total_fare: float
    surge_multiplier: float
    timestamp: datetime

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Ride Pricing API is running!",
        "status": "active",
        "model_loaded": model is not None,
        "endpoints": {
            "/": "This page",
            "/health": "Health check",
            "/api/v1/price": "POST - Get price for a ride",
            "/docs": "Interactive API documentation"
        }
    }

# Health check
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "timestamp": datetime.now().isoformat()
    }

# Pricing endpoint
@app.post("/api/v1/price", response_model=PricingResponse)
def get_price(request: PricingRequest):
    """Get dynamic price for a ride"""
    
    # Use current time if not provided
    if request.time_stamp is None:
        request.time_stamp = datetime.now()
    
    # Calculate base fare ($3 base + $1.5 per mile)
    base_fare = 3.0 + (request.ride.distance * 1.5)
    
    # Calculate surge multiplier based on time and weather
    surge = 1.0
    hour = request.time_stamp.hour
    
    # Rush hour factor (7-9 AM, 5-7 PM)
    if 7 <= hour <= 9 or 17 <= hour <= 19:
        surge *= 1.4
    
    # Late night factor (10 PM - 5 AM)
    if hour >= 22 or hour <= 5:
        surge *= 1.3
    
    # Weekend factor
    if request.time_stamp.weekday() >= 5:
        surge *= 1.15
    
    # Weather factors
    if request.weather.rain > 0.5:
        surge *= 1.3
    if request.weather.rain > 2.0:
        surge *= 1.2
    if request.weather.temp > 30 or request.weather.temp < 5:
        surge *= 1.1
    
    # Apply surge to base fare
    final_price = base_fare * surge
    
    # Ensure minimum price
    final_price = max(final_price, 3.0)
    
    return PricingResponse(
        ride_type=request.ride.ride_type,
        source=request.ride.source,
        destination=request.ride.destination,
        distance=round(request.ride.distance, 2),
        base_fare=round(base_fare, 2),
        total_fare=round(final_price, 2),
        surge_multiplier=round(surge, 2),
        timestamp=request.time_stamp
    )

# Run the app
if __name__ == "__main__":
    print("\n" + "="*50)
    print("Starting server...")
    print("="*50)
    print("\nAccess the API at:")
    print("  http://localhost:8000")
    print("  http://127.0.0.1:8000")
    print("\nAPI Documentation:")
    print("  http://localhost:8000/docs")
    print("\nPress CTRL+C to stop")
    print("="*50 + "\n")
    
    uvicorn.run(
        app, 
        host="127.0.0.1",
        port=8000,
        reload=True
    )