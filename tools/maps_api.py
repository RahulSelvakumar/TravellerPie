# tools/maps_api.py
import os
import requests
from dotenv import load_dotenv

# Load the API key securely
load_dotenv()
MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def get_place_details(place_name: str) -> dict:
    """
    Fetches real-world ratings and addresses for the AI to use in its itinerary.
    """
    if not MAPS_API_KEY or MAPS_API_KEY == "AIzaSyYourKeyHere...":
        return {"error": "API Key is missing or invalid."}

    # Hit the Google Maps Text Search API
    url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={place_name}&inputtype=textquery&fields=name,rating,formatted_address&key={MAPS_API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data.get("candidates"):
            candidate = data["candidates"][0]
            return {
                "name": candidate.get("name"),
                "rating": candidate.get("rating", "No rating available"),
                "address": candidate.get("formatted_address")
            }
        return {"error": f"Could not find details for {place_name}"}
    except Exception as e:
        return {"error": f"API request failed: {str(e)}"}

# Test it right now!
if __name__ == "__main__":
    print(get_place_details("Cubbon Park, Bengaluru"))