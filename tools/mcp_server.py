import os
import json
import requests
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

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

# mcp_server.py
# Initialize the LLM with Search Grounding capability
def get_search_agent():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", # Gr
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )

@mcp.tool()
async def get_live_events(city: str, month: str) -> str:
    """Fetches real-time local events using live search."""
    search_query = f"festivals and local events in {city} during {month} 2026"
    
    # FIX: Initialize the agent inside or pass it in
    agent = get_search_agent()
    
    try:
        # Using simple ainvoke to get grounded search results
        response = await agent.ainvoke([
            HumanMessage(content=f"Search for and list 3 specific events: {search_query}")
        ])
        
        if response.content:
            return json.dumps({"target_month": month, "live_events": response.content})
        return f"No events found for {city} in {month}."
    except Exception as e:
        return f"Search Error: {str(e)}"

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