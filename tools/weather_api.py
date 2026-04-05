# tools/weather_api.py
import requests

def get_current_weather(location: str) -> str:
    """
    Fetches the current weather for a city without needing an API key.
    """
    # wttr.in is a great free weather service for simple text data
    url = f"https://wttr.in/{location}?format=%C+%t"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
             return f"Current weather in {location}: {response.text}"
        return f"Could not fetch weather for {location}."
    except Exception as e:
        return "Weather data temporarily offline."

if __name__ == "__main__":
    print(get_current_weather("Bengaluru"))