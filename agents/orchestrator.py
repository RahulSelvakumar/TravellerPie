import json, operator, re, os, asyncio
from typing import Annotated, List, TypedDict, Sequence
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI

# 1. Load API Key from .env
load_dotenv()

# 2. DEFINE STATE FIRST (Fixes NameError)
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    preferences: List[str]

# 3. INITIALIZE MODEL
llm_base = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0
)
llm = llm_base.bind_tools([{"google_search": {}}])

# 4. DEFINE NODES
async def supervisor_node(state: AgentState):
    user_text = state['messages'][-1].content
    
    # Extract Origin to avoid 'Los Angeles' default
    origin_match = re.search(r'from\s+([a-zA-Z\s]+)', user_text, re.IGNORECASE)
    origin = origin_match.group(1).strip() if origin_match else "Bangalore"
    
    day_match = re.search(r'(\d+)\s*(?:day|days)?', user_text, re.IGNORECASE)
    num_days = day_match.group(1) if day_match else "3"

    system_prompt = f"""You are the TravellerPie Lead.
1. Use `Google Search` for 3 REAL flight options from {origin} to the destination for May 2026.
2. Structure JSON with airline, route, price, and link.
3. Plan {num_days} days of activities.

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
workflow.add_node("Supervisor", supervisor_node)
workflow.set_entry_point("Supervisor")
workflow.add_edge("Supervisor", END)
app = workflow.compile()

async def run_travel_agents(initial_state: dict):
    user_prompt = initial_state.get("prompt", "Trip from Bangalore")
    inputs = {
        "messages": [HumanMessage(content=user_prompt)],
        "preferences": initial_state.get("preferences", [])
    }
    try:
        final_state = await app.ainvoke(inputs)
        content = final_state["messages"][-1].content
        match = re.search(r'(\{.*\})', content, re.DOTALL)
        return match.group(1).strip() if match else content
    except Exception as e:
        print(f"❌ ORCHESTRATOR ERROR: {e}")
        return json.dumps({"morning_briefing": "Sync error."})