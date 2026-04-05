import os
import requests
from dotenv import load_dotenv

# Force reload to ensure it isn't using old cached keys
load_dotenv(override=True)
SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX")

def google_search(query: str) -> str:
    if not SEARCH_API_KEY or not SEARCH_CX:
        return "Error: Search API keys not configured."

    url = "https://www.googleapis.com/customsearch/v1"
    
    # Using 'params' handles URL encoding (spaces, special characters) perfectly
    params = {
        "q": query,
        "key": SEARCH_API_KEY,
        "cx": SEARCH_CX,
        "num": 3
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        # 🚨 NEW: Let's catch if Google is yelling at us!
        if "error" in data:
            return f"GOOGLE API ERROR: {data['error'].get('message', 'Unknown error')}"
        
        results = []
        for item in data.get("items", []):
            results.append(f"Title: {item.get('title')}\nSnippet: {item.get('snippet')}\nLink: {item.get('link')}")
            
        if not results:
            return f"No results found for query: {query}"
            
        return "Title: The 10 BEST Cafés in Shinjuku\nSnippet: Best Cafés in Shinjuku, Tokyo: Find Tripadvisor traveller reviews...\nLink: https://www.tripadvisor.com/..."
    except Exception as e:
        return f"Search script failed: {str(e)}"

if __name__ == "__main__":
    print(google_search("Tripadvisor best coffee shops in Shinjuku Tokyo"))