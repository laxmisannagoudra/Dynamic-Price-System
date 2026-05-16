# test_price.py
import requests
import json

print("="*50)
print("TESTING RIDE PRICING API")
print("="*50)

# API endpoint
url = "http://localhost:8000/api/v1/price"

# Test request
payload = {
    "ride": {
        "source": "North Station",
        "destination": "South Station",
        "distance": 3.5,
        "ride_type": "Lyft"
    },
    "weather": {
        "temp": 25,
        "rain": 0,
        "humidity": 0.6,
        "wind": 8
    }
}

print("\nSending request...")
print(json.dumps(payload, indent=2))

try:
    response = requests.post(url, json=payload)
    print(f"\nResponse Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n" + "="*50)
        print("PRICE RESULT")
        print("="*50)
        print(f"From: {result['source']}")
        print(f"To: {result['destination']}")
        print(f"Distance: {result['distance']} miles")
        print(f"Base Fare: ${result['base_fare']}")
        print(f"Surge Multiplier: {result['surge_multiplier']}x")
        print(f"TOTAL FARE: ${result['total_fare']}")
        print("="*50)
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Connection error: {e}")
    print("\nMake sure API is running:")
    print("  uvicorn main:app --reload")