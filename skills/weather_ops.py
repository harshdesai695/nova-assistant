import os
import requests
from core.registry import skill

@skill
def get_weather(city: str):
    """
    Fetches the current weather for a specific city using OpenWeatherMap.
    Args:
        city: The name of the city (e.g., 'London', 'New York', 'Tokyo').
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Error: OPENWEATHER_API_KEY not found in .env settings."

    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }

    try:
        response = requests.get(base_url, params=params)
        data = response.json()

        if response.status_code == 200:
            temp = data["main"]["temp"]
            condition = data["weather"][0]["description"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]
            
            return f"The current weather in {city} is {condition} with a temperature of {temp}°C. Humidity is {humidity}% and wind speed is {wind_speed} m/s."
        elif response.status_code == 404:
            return f"I couldn't find weather data for '{city}'. Please check the city name."
        else:
            return f"Weather service error: {data.get('message', 'Unknown error')}"

    except Exception as e:
        return f"Failed to connect to weather service: {str(e)}"