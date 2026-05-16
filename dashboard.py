# dashboard.py - Fixed version with proper column handling
from urllib import request

import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import numpy as np

st.set_page_config(page_title="Ride Pricing Dashboard", layout="wide")

st.title("🚕 Ride-Sharing Dynamic Pricing Dashboard")
st.markdown("---")

# Exchange rate (1 USD = 83.5 INR)
USD_TO_INR = 83.5

# Currency selector in sidebar
st.sidebar.header("Settings")
currency = st.sidebar.radio(
    "Select Currency",
    ["USD ($)", "INR (₹)"],
    index=0  # Default to USD
)

st.sidebar.markdown("---")
st.sidebar.header("Ride Details")

# Ride inputs
source = st.sidebar.selectbox(
    "Pickup Location",
    ["North Station", "South Station", "Back Bay", "Fenway", "Beacon Hill", 
     "West End", "Haymarket Square", "Theatre District", "Financial District"]
)

destination = st.sidebar.selectbox(
    "Dropoff Location",
    ["North Station", "South Station", "Back Bay", "Fenway", "Beacon Hill", 
     "West End", "Haymarket Square", "Theatre District", "Financial District"]
)

distance = st.sidebar.number_input("Distance (miles)", min_value=0.5, max_value=20.0, value=2.5, step=0.5)

ride_type = st.sidebar.selectbox(
    "Ride Type",
    ["Lyft", "UberX", "Lyft XL", "UberXL", "Lux", "Black", "Shared", "Taxi"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Weather Conditions")

temp = st.sidebar.slider("Temperature (°C)", -10, 45, 20, 1)
rain = st.sidebar.slider("Rain (mm/h)", 0.0, 10.0, 0.0, 0.1)
humidity = st.sidebar.slider("Humidity (%)", 0, 100, 50, 5) / 100
wind = st.sidebar.slider("Wind Speed (m/s)", 0, 30, 5, 1)

st.sidebar.markdown("---")

# Calculate button
calculate = st.sidebar.button("Calculate Price", type="primary", use_container_width=True)

# Display current currency info
if currency == "USD ($)":
    st.sidebar.info("💵 Prices shown in US Dollars")
else:
    st.sidebar.info(f"🇮🇳 Prices shown in Indian Rupees (1 USD = ₹{USD_TO_INR})")

# Main content area
col1, col2, col3 = st.columns(3)

if calculate:
    # API request
    api_url = "http://localhost:8000/api/v1/price"
    
    payload = {
        "ride": {
            "source": source,
            "destination": destination,
            "distance": distance,
            "ride_type": ride_type
        },
        "weather": {
            "temp": temp,
            "rain": rain,
            "humidity": humidity,
            "wind": wind
        },
        "time_stamp": datetime.now().isoformat()
    }
    
    with st.spinner("Calculating price..."):
        try:
            response = requests.post(api_url, json=payload, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                
                # Get USD values from API
                base_fare_usd = result['base_fare']
                total_fare_usd = result['total_fare']
                surge = result['surge_multiplier']
                
                # Convert to INR if needed
                if currency == "INR (₹)":
                    base_fare = base_fare_usd * USD_TO_INR
                    total_fare = total_fare_usd * USD_TO_INR
                    currency_symbol = "₹"
                else:
                    base_fare = base_fare_usd
                    total_fare = total_fare_usd
                    currency_symbol = "$"
                
                # Column 1 - Trip Info
                with col1:
                    st.metric("📍 From", result['source'])
                    st.metric("📍 To", result['destination'])
                    st.metric("📏 Distance", f"{result['distance']} miles")
                    st.metric("⏱️ Time", result['timestamp'][11:16])
                
                # Column 2 - Pricing Details
                with col2:
                    st.metric("💰 Base Fare", f"{currency_symbol}{base_fare:.2f}")
                    st.metric("⚡ Surge Multiplier", f"{surge}x")
                    
                    # Show surge reason
                    if surge > 1.0:
                        surge_reasons = []
                        hour = datetime.now().hour
                        if 7 <= hour <= 9 or 17 <= hour <= 19:
                            surge_reasons.append("🚗 Rush Hour")
                        if hour >= 22 or hour <= 5:
                            surge_reasons.append("🌙 Late Night")
                        if datetime.now().weekday() >= 5:
                            surge_reasons.append("📅 Weekend")
                        if rain > 0.5:
                            surge_reasons.append("☔ Rain")
                        if temp > 30 or temp < 5:
                            surge_reasons.append("🌡️ Extreme Temp")
                        
                        if surge_reasons:
                            st.caption(f"Surge factors: {', '.join(surge_reasons)}")
                
                # Column 3 - Total
                with col3:
                    st.metric("💵 TOTAL FARE", f"{currency_symbol}{total_fare:.2f}", 
                             delta=f"{surge}x surge", delta_color="normal")
                    st.metric("🚕 Ride Type", result['ride_type'])
                    
                    # Show both currencies
                    if currency == "INR (₹)":
                        st.caption(f"USD: ${total_fare_usd:.2f}")
                    else:
                        st.caption(f"INR: ₹{total_fare_usd * USD_TO_INR:.2f}")
                
                # Detailed breakdown
                st.markdown("---")
                st.subheader("💰 Price Breakdown")
                
                # Create columns for breakdown
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    st.info(f"**Base Calculation**\n\n"
                           f"• Base rate: $3.00\n"
                           f"• Per mile: $1.50\n"
                           f"• Distance: {distance} miles\n"
                           f"• Base fare: ${base_fare_usd:.2f}")
                
                with col_b:
                    st.warning(f"**Surge Factors**\n\n"
                              f"• Rush hour: +40%\n"
                              f"• Late night: +30%\n"
                              f"• Weekend: +15%\n"
                              f"• Rain: +30%\n"
                              f"• Total surge: {surge}x")
                
                with col_c:
                    if currency == "INR (₹)":
                        st.success(f"**Final Price**\n\n"
                                  f"• USD: ${total_fare_usd:.2f}\n"
                                  f"• Exchange: 1 USD = ₹{USD_TO_INR}\n"
                                  f"• INR: ₹{total_fare:.2f}")
                    else:
                        st.success(f"**Final Price**\n\n"
                                  f"• USD: ${total_fare:.2f}\n"
                                  f"• INR: ₹{total_fare_usd * USD_TO_INR:.2f}\n"
                                  f"• Exchange: 1 USD = ₹{USD_TO_INR}")
                
                # FIXED: Price Comparison Section
                st.markdown("---")
                st.subheader("📊 Price Comparison")
                
                # Create comparison dataframe with proper column names
                comparison_data = {
                    "Component": ["Base Fare", "Surge Amount", "Total Fare"],
                    "Value (USD)": [
                        base_fare_usd, 
                        total_fare_usd - base_fare_usd, 
                        total_fare_usd
                    ],
                    "Value (INR)": [
                        base_fare_usd * USD_TO_INR, 
                        (total_fare_usd - base_fare_usd) * USD_TO_INR, 
                        total_fare_usd * USD_TO_INR
                    ]
                }
                comparison_df = pd.DataFrame(comparison_data)
                
                # Display the dataframe
                st.dataframe(comparison_df, use_container_width=True)
                
                # Create bar chart based on selected currency
                st.subheader("📈 Price Visualization")
                
                if currency == "USD ($)":
                    chart_data = comparison_df[["Component", "Value (USD)"]].copy()
                    chart_data.columns = ["Component", "Amount (USD)"]
                    st.bar_chart(chart_data.set_index("Component"))
                    st.caption("Amounts shown in US Dollars (USD)")
                else:
                    chart_data = comparison_df[["Component", "Value (INR)"]].copy()
                    chart_data.columns = ["Component", "Amount (INR)"]
                    st.bar_chart(chart_data.set_index("Component"))
                    st.caption(f"Amounts shown in Indian Rupees (INR) @ 1 USD = ₹{USD_TO_INR}")
                
                # Add pie chart for better visualization
                st.subheader("🥧 Price Distribution")
                
                # Prepare data for pie chart
                pie_data = pd.DataFrame({
                    "Component": ["Base Fare", "Surge"],
                    "Amount": [base_fare_usd, total_fare_usd - base_fare_usd]
                })
                
                if currency == "INR (₹)":
                    pie_data["Amount"] = pie_data["Amount"] * USD_TO_INR
                    pie_label = "Amount (₹)"
                else:
                    pie_label = "Amount ($)"
                
                st.dataframe(pie_data, use_container_width=True)
                
                # Simple bar for surge comparison
                surge_data = pd.DataFrame({
                    "Factor": ["Base", "With Surge"],
                    "Price": [base_fare_usd, total_fare_usd]
                })
                
                if currency == "INR (₹)":
                    surge_data["Price"] = surge_data["Price"] * USD_TO_INR
                    st.bar_chart(surge_data.set_index("Factor"))
                    st.caption(f"Impact of {surge}x surge on price (INR)")
                else:
                    st.bar_chart(surge_data.set_index("Factor"))
                    st.caption(f"Impact of {surge}x surge on price (USD)")
                
            else:
                st.error(f"API Error: {response.status_code}")
                st.json(response.text)
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to API!")
            st.info("Make sure the API server is running: `uvicorn main:app --reload`")
        except requests.exceptions.Timeout:
            st.error("⏰ Request timed out. Please try again.")
        except Exception as e:
            st.error(f"Error: {e}")
else:
    # Show initial state
    with col1:
        st.info("👈 **Enter ride details**\n\n"
                "1. Select pickup/dropoff\n"
                "2. Set distance\n"
                "3. Choose ride type")
    
    with col2:
        st.info("🌤️ **Adjust weather**\n\n"
                "• Temperature\n"
                "• Rain intensity\n"
                "• Humidity\n"
                "• Wind speed")
    
    with col3:
        st.info("💰 **Click Calculate**\n\n"
                f"• View price in {currency}\n"
                "• See surge factors\n"
                "• Compare both currencies")
    
    # Show sample price for current currency
    st.markdown("---")
    st.subheader("📈 Sample Price Estimates")
    
    sample_distances = [1, 2, 3, 5, 8, 10]
    sample_prices_usd = [3.0 + d * 1.5 for d in sample_distances]
    
    if currency == "INR (₹)":
        sample_prices = [p * USD_TO_INR for p in sample_prices_usd]
        symbol = "₹"
    else:
        sample_prices = sample_prices_usd
        symbol = "$"
    
    sample_data = pd.DataFrame({
        "Distance (miles)": sample_distances,
        f"Est. Price ({symbol})": [f"{symbol}{p:.2f}" for p in sample_prices],
        "USD ($)": [f"${p:.2f}" for p in sample_prices_usd],
        "INR (₹)": [f"₹{p * USD_TO_INR:.2f}" for p in sample_prices_usd]
    })
    st.dataframe(sample_data, use_container_width=True)
    
    st.caption("Note: Actual price may vary based on time, weather, and surge conditions")

# Footer
st.markdown("---")
st.caption("Dynamic Pricing Engine | Real-time price optimization | Powered by ML")
