import os
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool

# --- 1. Tools (The "Hands") ---
# These are mocks. Connect them to your /tools/ directory later.

@tool
def get_flight_info(origin: str, destination: str, date: str):
    """Fetch flight availability and pricing."""
    return f"Flight AI-101 from {origin} to {destination} on {date} is confirmed. Price: $450."

@tool
def get_local_weather(location: str):
    """Get real-time weather and alerts for a city."""
    return f"Weather in {location}: 28°C, Humidity 60%. Perfect for outdoor tours."

@tool
def search_events(city: str):
    """Find local events, festivals, or concerts."""
    return f"Events in {city}: Jazz Festival at Central Park, Tech Expo at Downtown."

# --- 2. Sub-Agent Logic ---

class TravellerSubAgents:
    def __init__(self):
        # Flash is used for sub-agents to keep the hackathon costs/latency low
        self.llm = ChatVertexAI(model_name="gemini-1.5-flash-preview-0409", temperature=0)

    def transit_agent(self, messages):
        agent = self.llm.bind_tools([get_flight_info])
        prompt = SystemMessage(content="You are the Transit Agent. Optimize routes and travel times.")
        return agent.invoke([prompt] + messages)

    def intel_agent(self, messages):
        agent = self.llm.bind_tools([get_local_weather, search_events])
        prompt = SystemMessage(content="You are the Local Intel Agent. Provide weather-safe recommendations.")
        return agent.invoke([prompt] + messages)

    def planning_agent(self, messages):
        # Planning usually synthesizes data into a timeline
        prompt = SystemMessage(content="You are the Planning Agent. Box activities into a 24-hour itinerary.")
        return self.llm.invoke([prompt] + messages)