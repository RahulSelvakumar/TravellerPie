# agents/sub_agents.py
import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage
from langchain_core.tools import tool

# 1. Import your real-time tools
from tools.weather_api import get_current_weather
from tools.search_api import google_search
from tools.transit_api import get_real_google_flights
from tools.events_api import get_local_events
from tools.maps_api import get_place_details

load_dotenv()

# --- TOOL WRAPPERS ---
@tool
def tool_weather(location: str) -> str:
    """Get real-time weather for a city."""
    return get_current_weather(location)

@tool
def tool_search(query: str) -> str:
    """Search the web for events, highly-rated cafes, design spots, or specific local news."""
    return google_search(query)

@tool
def tool_transit(origin: str, destination: str, date: str) -> str:
    """Find real flight options from a starting city to a destination on a specific date."""
    return str(get_real_google_flights(origin, destination, date))

@tool
def tool_events(city: str, month: str) -> str:
    """Find local festivals, concerts, or exhibitions in a city."""
    return get_local_events(city, month)

@tool
def tool_maps(place_name: str) -> str:
    """Get Google Maps ratings and exact addresses for hotels or restaurants."""
    return str(get_place_details(place_name))


# --- THE SUB-AGENT CLASS ---
class TravellerSubAgents:
    def __init__(self):
        # Use Flash for speed and higher rate limits
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0
        )

    def _run_agent(self, tools, system_prompt, messages):
        """A robust, manual tool-calling loop for the agents."""
        llm_with_tools = self.llm.bind_tools(tools)
        
        # Ensure we are passing the conversation history
        current_messages = [SystemMessage(content=system_prompt)] + messages

        # Allow the agent to think and call tools up to 3 times
        for _ in range(3):
            response = llm_with_tools.invoke(current_messages)
            current_messages.append(response)

            if not response.tool_calls:
                break

            for tool_call in response.tool_calls:
                selected_tool = next((t for t in tools if t.name == tool_call["name"]), None)
                if selected_tool:
                    print(f"🔧 [SUB-AGENT] Executing {tool_call['name']}...")
                    tool_result = selected_tool.invoke(tool_call["args"])
                    current_messages.append(ToolMessage(
                        tool_call_id=tool_call["id"],
                        name=tool_call["name"],
                        content=str(tool_result)
                    ))
        
        return AIMessage(content=current_messages[-1].content)

    def transit_agent(self, messages, preferences=[]):
        pref_context = f"User Preferences: {', '.join(preferences)}."
        prompt = (
            f"You are the Transit Agent. {pref_context} "
            "Use tool_transit for flights and tool_search for general logistics. "
            "Suggest the best ways to move between locations based on user style."
        )
        return self._run_agent([tool_transit, tool_search], prompt, messages)

    def intel_agent(self, messages, preferences=[]):
        pref_context = f"User Preferences: {', '.join(preferences)}."
        prompt = (
            f"You are the Local Intel Agent. {pref_context} "
            "Use tool_search, tool_events, and tool_weather. "
            "Find hidden gems, specific cafes (if coffee addict), or indoor spots (if raining)."
        )
        return self._run_agent([tool_search, tool_events, tool_weather], prompt, messages)

    def planning_agent(self, messages, preferences=[]):
        pref_context = f"User Preferences: {', '.join(preferences)}."
        prompt = (
            f"You are the Planning Agent. {pref_context} "
            "Use tool_maps to verify locations and tool_search to check opening times. "
            "Combine all data into a cohesive, high-detail plan for specific days."
        )
        return self._run_agent([tool_maps, tool_search], prompt, preferences, messages)