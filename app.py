import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Open-Meteo Weather Dashboard",
    page_icon="⛅",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .weather-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .big-temp {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .weather-metric {
        font-size: 1.2rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Weather code descriptions
WEATHER_CODES = {
    0: "☀️ Clear sky",
    1: "🌤️ Mainly clear",
    2: "⛅ Partly cloudy",
    3: "☁️ Overcast",
    45: "🌫️ Foggy",
    48: "🌫️ Depositing rime fog",
    51: "🌦️ Light drizzle",
    53: "🌦️ Moderate drizzle",
    55: "🌧️ Dense drizzle",
    61: "🌧️ Slight rain",
    63: "🌧️ Moderate rain",
    65: "🌧️ Heavy rain",
    71: "🌨️ Slight snow",
    73: "🌨️ Moderate snow",
    75: "❄️ Heavy snow",
    77: "🌨️ Snow grains",
    80: "🌦️ Slight rain showers",
    81: "🌧️ Moderate rain showers",
    82: "⛈️ Violent rain showers",
    85: "🌨️ Slight snow showers",
    86: "❄️ Heavy snow showers",
    95: "⛈️ Thunderstorm",
    96: "⛈️ Thunderstorm with hail",
    99: "⛈️ Thunderstorm with heavy hail"
}

@st.cache_data(ttl=1800)
def get_weather_data(latitude, longitude):
    """Fetch weather data from Open-Meteo API"""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
        "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
        "timezone": "auto"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching weather data: {e}")
        return None

@st.cache_data(ttl=3600)
def geocode_location(city_name):
    """Geocode city name to coordinates using Open-Meteo Geocoding API"""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": city_name,
        "count": 5,
        "language": "en",
        "format": "json"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('results'):
            return data['results']
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error geocoding location: {e}")
        return None

def display_current_weather(weather_data):
    """Display current weather conditions"""
    current = weather_data['current']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("<div class='weather-card'>", unsafe_allow_html=True)
        weather_code = current.get('weather_code', 0)
        weather_desc = WEATHER_CODES.get(weather_code, "Unknown")
        st.markdown(f"<div style='font-size: 2rem;'>{weather_desc}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='big-temp'>{current['temperature_2m']}°C</div>", unsafe_allow_html=True)
        st.markdown(f"Feels like: {current['apparent_temperature']}°C")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='weather-card'>", unsafe_allow_html=True)
        st.markdown("### 💧 Humidity")
        st.markdown(f"<div class='weather-metric'>{current['relative_humidity_2m']}%</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='weather-card'>", unsafe_allow_html=True)
        st.markdown("### 💨 Wind Speed")
        st.markdown(f"<div class='weather-metric'>{current['wind_speed_10m']} km/h</div>", unsafe_allow_html=True)
        st.markdown(f"Direction: {current['wind_direction_10m']}°")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col4:
        st.markdown("<div class='weather-card'>", unsafe_allow_html=True)
        st.markdown("### 🌧️ Precipitation")
        st.markdown(f"<div class='weather-metric'>{current['precipitation']} mm</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

def display_hourly_forecast(weather_data):
    """Display hourly forecast chart"""
    hourly = weather_data['hourly']
    
    # Create DataFrame for next 24 hours
    df = pd.DataFrame({
        'time': pd.to_datetime(hourly['time'][:24]),
        'temperature': hourly['temperature_2m'][:24],
        'precipitation': hourly['precipitation'][:24],
        'humidity': hourly['relative_humidity_2m'][:24]
    })
    
    # Temperature chart
    fig_temp = go.Figure()
    fig_temp.add_trace(go.Scatter(
        x=df['time'],
        y=df['temperature'],
        mode='lines+markers',
        name='Temperature',
        line=dict(color='#FF6B6B', width=3),
        marker=dict(size=6)
    ))
    fig_temp.update_layout(
        title='24-Hour Temperature Forecast',
        xaxis_title='Time',
        yaxis_title='Temperature (°C)',
        height=400,
        hovermode='x unified'
    )
    st.plotly_chart(fig_temp, use_container_width=True)
    
    # Precipitation and Humidity chart
    fig_precip = go.Figure()
    fig_precip.add_trace(go.Bar(
        x=df['time'],
        y=df['precipitation'],
        name='Precipitation',
        marker_color='#4ECDC4'
    ))
    fig_precip.add_trace(go.Scatter(
        x=df['time'],
        y=df['humidity'],
        name='Humidity',
        yaxis='y2',
        line=dict(color='#95E1D3', width=2)
    ))
    fig_precip.update_layout(
        title='24-Hour Precipitation & Humidity Forecast',
        xaxis_title='Time',
        yaxis_title='Precipitation (mm)',
        yaxis2=dict(title='Humidity (%)', overlaying='y', side='right'),
        height=400,
        hovermode='x unified'
    )
    st.plotly_chart(fig_precip, use_container_width=True)

def display_daily_forecast(weather_data):
    """Display 7-day forecast"""
    daily = weather_data['daily']
    
    st.markdown("### 📅 7-Day Forecast")
    
    df_daily = pd.DataFrame({
        'Date': pd.to_datetime(daily['time']),
        'Max Temp (°C)': daily['temperature_2m_max'],
        'Min Temp (°C)': daily['temperature_2m_min'],
        'Precipitation (mm)': daily['precipitation_sum'],
        'Max Wind (km/h)': daily['wind_speed_10m_max'],
        'Weather': [WEATHER_CODES.get(code, "Unknown") for code in daily['weather_code']]
    })
    
    df_daily['Date'] = df_daily['Date'].dt.strftime('%Y-%m-%d (%a)')
    
    st.dataframe(df_daily, use_container_width=True, hide_index=True)
    
    # Temperature range chart
    fig_daily = go.Figure()
    dates = pd.to_datetime(daily['time'])
    
    fig_daily.add_trace(go.Scatter(
        x=dates,
        y=daily['temperature_2m_max'],
        mode='lines+markers',
        name='Max Temp',
        line=dict(color='#FF6B6B', width=2),
        marker=dict(size=8)
    ))
    fig_daily.add_trace(go.Scatter(
        x=dates,
        y=daily['temperature_2m_min'],
        mode='lines+markers',
        name='Min Temp',
        line=dict(color='#4ECDC4', width=2),
        marker=dict(size=8)
    ))
    fig_daily.update_layout(
        title='7-Day Temperature Range',
        xaxis_title='Date',
        yaxis_title='Temperature (°C)',
        height=400,
        hovermode='x unified'
    )
    st.plotly_chart(fig_daily, use_container_width=True)

def main():
    # Header
    st.markdown("<div class='main-header'>⛅ Open-Meteo Interactive Weather Dashboard</div>", 
                unsafe_allow_html=True)
    st.markdown("지도에서 위치를 클릭하면 해당 지역의 시간별 기온 데이터를 볼러옵니다.")
    
    # Sidebar
    with st.sidebar:
        st.header("🌍 Location Selection")
        
        # Option 1: Search by city
        st.subheader("Search by City")
        city_name = st.text_input("Enter city name", placeholder="e.g., Seoul, Tokyo, New York")
        
        if city_name:
            locations = geocode_location(city_name)
            if locations:
                location_options = [
                    f"{loc['name']}, {loc.get('admin1', '')}, {loc['country']}"
                    for loc in locations
                ]
                selected_location = st.selectbox("Select location", location_options)
                selected_idx = location_options.index(selected_location)
                selected_loc = locations[selected_idx]
                
                if st.button("Get Weather", type="primary"):
                    st.session_state.latitude = selected_loc['latitude']
                    st.session_state.longitude = selected_loc['longitude']
                    st.session_state.location_name = selected_location
        
        st.markdown("---")
        
        # Option 2: Manual coordinates
        st.subheader("Or Enter Coordinates")
        manual_lat = st.number_input("Latitude", value=37.5665, format="%.4f")
        manual_lon = st.number_input("Longitude", value=126.9780, format="%.4f")
        
        if st.button("Use These Coordinates"):
            st.session_state.latitude = manual_lat
            st.session_state.longitude = manual_lon
            st.session_state.location_name = f"Lat: {manual_lat}, Lon: {manual_lon}"
        
        st.markdown("---")
        st.markdown("### 📍 Popular Cities")
        popular_cities = {
            "Seoul 🇰🇷": (37.5665, 126.9780),
            "Tokyo 🇯🇵": (35.6762, 139.6503),
            "New York 🇺🇸": (40.7128, -74.0060),
            "London 🇬🇧": (51.5074, -0.1278),
            "Paris 🇫🇷": (48.8566, 2.3522),
            "Sydney 🇦🇺": (-33.8688, 151.2093)
        }
        
        for city, (lat, lon) in popular_cities.items():
            if st.button(city, use_container_width=True):
                st.session_state.latitude = lat
                st.session_state.longitude = lon
                st.session_state.location_name = city
    
    # Initialize session state
    if 'latitude' not in st.session_state:
        st.session_state.latitude = 37.5665  # Seoul default
        st.session_state.longitude = 126.9780
        st.session_state.location_name = "Seoul, South Korea"
    
    # Display selected location
    st.info(f"📍 Selected Location: **{st.session_state.location_name}** (Lat: {st.session_state.latitude:.4f}, Lon: {st.session_state.longitude:.4f})")
    
    # Fetch and display weather data
    with st.spinner("Fetching weather data..."):
        weather_data = get_weather_data(st.session_state.latitude, st.session_state.longitude)
    
    if weather_data:
        # Current weather
        st.markdown("## 🌤️ Current Weather")
        display_current_weather(weather_data)
        
        st.markdown("---")
        
        # Hourly forecast
        st.markdown("## ⏰ Hourly Forecast")
        display_hourly_forecast(weather_data)
        
        st.markdown("---")
        
        # Daily forecast
        display_daily_forecast(weather_data)
        
        # Map
        st.markdown("---")
        st.markdown("## 🗺️ Location Map")
        map_df = pd.DataFrame({
            'lat': [st.session_state.latitude],
            'lon': [st.session_state.longitude]
        })
        st.map(map_df, zoom=8)
        
    else:
        st.error("Unable to fetch weather data. Please try again.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
    Data provided by <a href='https://open-meteo.com/'>Open-Meteo.com</a> | 
    Free Weather API for non-commercial use
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
