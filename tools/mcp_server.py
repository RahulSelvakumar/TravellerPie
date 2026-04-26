import os
import json
import requests
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Initialize the MCP Server
mcp = FastMCP("TravellerPie-Core")
load_dotenv()

# --- 1. Specialized Maps Tool ---
# We keep this because Google Grounding gives text, but this gives 
# structured JSON (ratings, address) for your UI cards.
@mcp.tool()
def get_place_details(place_name: str) -> dict:
    """
    Fetches ratings and formatted addresses for a specific hotel or restaurant.
    Use this to 'vet' locations mentioned in the itinerary.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"error": "Maps API key not found in environment."}
        
    url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": place_name,
        "inputtype": "textquery",
        "fields": "name,rating,formatted_address",
        "key": api_key
    }
    
    try:
        response = requests.get(url, params=params).json()
        if response.get("candidates"):
            candidate = response["candidates"][0]
            return {
                "name": candidate.get("name"),
                "rating": candidate.get("rating", "N/A"),
                "address": candidate.get("formatted_address")
            }
        return {"error": f"No specific details found for {place_name}"}
    except Exception as e:
        return {"error": str(e)}

# --- 2. Local/Private Events Database ---
# We keep this for 'curated' experiences that general search might miss.
@mcp.tool()
def get_curated_events(city: str, month: str) -> str:
    """
    Retrieves internal, curated local events database for specific cities.
    """
    db = {
        "tokyo": {"april": [{"event": "Ueno Park Sakura Night", "type": "Cultural"}]},
        "bengaluru": {"may": [{"event": "Indiranagar Jazz Night", "type": "Music"}]}
    }
    city_data = db.get(city.lower(), {})
    events = city_data.get(month.lower())
    
    if events:
        return json.dumps({"curated_events": events})
    return "No curated internal events. Suggest using Google Search Grounding for live web events."

# --- 3. Weather Fallback (Optional) ---
# Keeping this only as a lightweight backup to Grounding.
@mcp.tool()
def get_quick_weather(location: str) -> str:
    """Provides a quick temperature/condition snapshot for a location."""
    try:
        response = requests.get(f"https://wttr.in/{location}?format=%C+%t", timeout=5)
        if response.status_code == 200:
             return f"Quick Weather: {response.text}"
    except:
        pass
    return "Weather service busy. Recommend using Google Search Grounding."

if __name__ == "__main__":
    mcp.run()