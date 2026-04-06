import os, requests
from dotenv import load_dotenv

load_dotenv()
MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def get_place_details(place_name: str) -> dict:
    if not MAPS_API_KEY: return {"error": "Missing Maps API Key"}
    url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={place_name}&inputtype=textquery&fields=name,rating,formatted_address&key={MAPS_API_KEY}"
    try:
        response = requests.get(url).json()
        if response.get("candidates"):
            c = response["candidates"][0]
            return {"name": c.get("name"), "rating": c.get("rating", "N/A"), "address": c.get("formatted_address")}
        return {"error": "Not found"}
    except Exception as e:
        return {"error": str(e)}