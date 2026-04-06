import requests
import os

def get_real_google_flights(origin, destination, date):
    api_key = os.getenv("GOOGLE_API_KEY")
    search_engine_id = os.getenv("GOOGLE_SEARCH_API_KEY")
    query = f"flights from {origin} to {destination} on {date}"
    
    url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={search_engine_id}&q={query}"
    
    response = requests.get(url).json()
    # The agent will parse 'items' to find flight numbers and prices
    return response.get('items', [])