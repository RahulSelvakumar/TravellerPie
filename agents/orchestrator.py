import json, operator, re, os, asyncio
from typing import Annotated, List, TypedDict, Sequence
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI

# 1. Load API Key
load_dotenv()

# 2. DEFINE STATE
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    preferences: List[str]
    # Adding specific fields to state for dynamic access across nodes
    origin: str
    destination: str
    num_days: int

# 3. INITIALIZE MODEL (Lazy - will be initialized on first use)
_llm = None

def get_llm():
    global _llm
    if _llm is None:
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            print("⚠️  WARNING: GOOGLE_API_KEY not set. LLM calls will fail at runtime.")
            google_api_key = "placeholder_key_for_startup"
        
        _llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0
        )
    return _llm

async def fetch_events_node(state: AgentState):
    """Parses the prompt for a month and calls the live search tool."""
    from tools.mcp_server import get_live_events
    
    user_prompt = state['messages'][0].content
    destination = state.get("destination", "Japan")
    
    # Regex to find month names in the prompt
    months = ["january", "february", "march", "april", "may", "june", 
              "july", "august", "september", "october", "november", "december"]
    month_match = re.search(r'\b(' + '|'.join(months) + r')\b', user_prompt, re.I)
    
    # Use detected month or hardcode "May" if not found
    target_month = month_match.group(1).capitalize() if month_match else "May"
    
    print(f"🔍 [Agent] Fetching live events for {destination} in {target_month}...")
    events_json = await get_live_events(destination, target_month)
    
    return {"live_events": events_json}

# 4. DEFINE NODES
async def supervisor_node(state: AgentState):
    # Get LLM instance
    llm = get_llm()
    origin = state.get("origin", "Bangalore")
    destination = state.get("destination", "Japan")
    num_days = state.get("num_days", 4)
    interests = state.get("preferences", [])
    
    # Create a strict constraint string
    constraint_block = "GENERAL TOURISM"
    if interests:
        constraint_block = f"MANDATORY: You MUST include specific activities for: {', '.join(interests)}."
        live_events = state.get("live_events", "No specific local festivals found.")

    system_prompt = f"""You are the TravellerPie Lead. {constraint_block}
     LIVE DATA FROM SEARCH AGENT:
    {live_events}
    RULES:
    - If 'gym' is a constraint, find a specific high-end gym or hotel with a 24/7 fitness center in the destination.
    - If 'minimalist' is a constraint, avoid cluttered markets; choose modern architecture.
    - Ensure the hotel is suggested based on the day's activities and is located conveniently.
    - Ensure the 'hotel' field in the JSON matches the specific hotel for that day.
    - Plan a {state.get('num_days')} day trip from {origin}.

1. Plan a trip from {origin} to {destination}.
2. Use your knowledge to provide 3 REALISTIC flight options for May 2026.
3. Structure JSON with airline, route, price, and link.
4. Plan {num_days} days of activities.
5. For each day, include a hotel recommendation and 3 activities (morning, afternoon, evening).
6. Use ONLY the information from the messages and your internal knowledge. Do NOT make up information.
CRITICAL: You must return ONLY valid JSON. Do not include markdown code blocks.
    The JSON keys MUST match exactly: 'morning_briefing', 'logistics', and 'days'.
    In 'logistics', include 3 flight options with valid links.

Return ONLY raw JSON:
{{
  "morning_briefing": "...",
  "logistics": [ {{ "airline": "..", "route": "..", "price": "..", "link": ".." }} ],
  "days": [ {{ "day_number": 1, "hotel": "..", "morning": "..", "afternoon": "..", "evening": ".." }} ],
  "sources": []
}}"""

    response = await llm.ainvoke([SystemMessage(content=system_prompt)] + state['messages'])
    return {"messages": [response]}

# 5. COMPILE GRAPH
workflow = StateGraph(AgentState)
workflow.add_node("FetchEvents", fetch_events_node)
workflow.add_node("Supervisor", supervisor_node)

workflow.set_entry_point("FetchEvents")
workflow.add_edge("FetchEvents", "Supervisor")
workflow.add_edge("Supervisor", END)
graph_app = workflow.compile()

# 6. DYNAMIC ORCHESTRATOR
async def run_travel_agents(initial_state: dict):
    user_prompt = initial_state.get("prompt", "")
    
    # --- DYNAMIC EXTRACTION LAYER ---
    # Using regex to find common patterns for origin, destination, and days
    # Example: "from Bangalore to Japan for 5 days"
    origin_match = re.search(r'from\s+([a-zA-Z\s]+?)(?=\s+to|\s+for|$)', user_prompt, re.I)
    dest_match = re.search(r'to\s+([a-zA-Z\s]+?)(?=\s+for|\s+from|$)', user_prompt, re.I)
    days_match = re.search(r'(\d+)\s+day', user_prompt, re.I)

    origin = origin_match.group(1).strip() if origin_match else "Bangalore"
    destination = dest_match.group(1).strip() if dest_match else "Japan"
    num_days = int(days_match.group(1)) if days_match else 4

    inputs = {
        "messages": [HumanMessage(content=user_prompt)],
        "preferences": initial_state.get("preferences", []),
        "origin": origin,
        "destination": destination,
        "num_days": num_days
    }
    
    try:
        final_state = await graph_app.ainvoke(inputs)
        content = final_state["messages"][-1].content
        # Scrubber to ensure clean JSON is returned to the UI
        match = re.search(r'(\{.*\})', content, re.DOTALL)
        return match.group(1).strip() if match else content
    except Exception as e:
        print(f"❌ ORCHESTRATOR ERROR: {e}")
        return json.dumps({"morning_briefing": f"Sync error: {str(e)}"})