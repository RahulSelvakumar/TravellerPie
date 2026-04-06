import os, requests
from dotenv import load_dotenv

load_dotenv()
SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX")

def google_search(query: str) -> str:
    if not SEARCH_API_KEY or not SEARCH_CX: return "Error: Missing Search Keys"
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"q": query, "key": SEARCH_API_KEY, "cx": SEARCH_CX, "num": 3}
    try:
        data = requests.get(url, params=params).json()
        if "error" in data: return f"API ERROR: {data['error'].get('message')}"
        results = [f"Title: {i.get('title')}\nSnippet: {i.get('snippet')}" for i in data.get("items", [])]
        return "\n\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Search failed: {str(e)}"