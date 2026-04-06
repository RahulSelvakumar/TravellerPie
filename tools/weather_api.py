import requests

def get_current_weather(location: str) -> str:
    url = f"https://wttr.in/{location}?format=%C+%t"
    try:
        response = requests.get(url)
        if response.status_code == 200:
             return f"Current weather in {location}: {response.text}"
        return f"Could not fetch weather for {location}."
    except Exception:
        return "Weather data temporarily offline."