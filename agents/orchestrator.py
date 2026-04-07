# agents/orchestrator.py
from collections.abc import Sequence
import json, operator, re
from typing import Annotated, List, TypedDict, Union
import os, time
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

load_dotenv()

# 1. Define the State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    preferences: List[str]
    next: str 

# 2. Define the Nodes
from agents.sub_agents import TravellerSubAgents
sub_agents = TravellerSubAgents()
supervisor_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0,google_api_key=os.getenv("GOOGLE_API_KEY"))

def call_transit(state: AgentState):
    time.sleep(1)
    response = sub_agents.transit_agent(state['messages'])
    return {"messages": [HumanMessage(content=response.content, name="TransitAgent")]}

def call_intel(state: AgentState):
    time.sleep(1)
    response = sub_agents.intel_agent(state['messages'])
    return {"messages": [HumanMessage(content=response.content, name="LocalIntelAgent")]}

def call_planning(state: AgentState):
    time.sleep(1)
    response = sub_agents.planning_agent(state['messages'])
    return {"messages": [HumanMessage(content=response.content, name="PlanningAgent")]}

def supervisor_node(state: AgentState):
    user_prefs = state.get('preferences', [])
    prefs_str = ", ".join(user_prefs) if user_prefs else "None"
    
    # AGGRESSIVE PROMPT: Demands JSON and forbids conversation
    system_prompt = (
        f"User Context: {prefs_str}. "
        "You are the TravellerPie Executive Lead. "
        "DECISION RULE: \n"
        "1. If you need more data, output ONLY the word 'TRANSIT', 'INTEL', or 'PLANNING'.\n"
        "2. If you have enough info, output a LUXURY ITINERARY in STRICT RAW JSON format ONLY.\n"
        "JSON KEYS: 'morning_briefing', 'itinerary' (list of objects with: day, hotel, morning, afternoon, evening, snack).\n"
        "CRITICAL: Do NOT include any conversational text, 'Excellent', or markdown code blocks."
    )
    
    messages = [SystemMessage(content=system_prompt)] + state['messages']
    response = supervisor_llm.invoke(messages)
    content = response.content.strip()
    
    # Routing Logic
    if "{" in content:
        return {"next": END, "messages": [response]}
    
    upper_content = content.upper()
    if "TRANSIT" in upper_content:
        return {"next": "TransitAgent", "messages": [response]}
    if "INTEL" in upper_content or "LOCAL" in upper_content:
        return {"next": "LocalIntelAgent", "messages": [response]}
    
    # Default to Planning if it's being vague
    return {"next": "PlanningAgent", "messages": [response]}

# 3. Build the Graph
workflow = StateGraph(AgentState)
workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("TransitAgent", call_transit)
workflow.add_node("LocalIntelAgent", call_intel)
workflow.add_node("PlanningAgent", call_planning)

workflow.add_edge("TransitAgent", "Supervisor")
workflow.add_edge("LocalIntelAgent", "Supervisor")
workflow.add_edge("PlanningAgent", "Supervisor")

workflow.add_conditional_edges(
    "Supervisor",
    lambda x: x["next"],
    {
        "TransitAgent": "TransitAgent",
        "LocalIntelAgent": "LocalIntelAgent",
        "PlanningAgent": "PlanningAgent",
        END: END
    }
)

workflow.set_entry_point("Supervisor")
app = workflow.compile() 

def run_travel_agents(initial_state: dict):
    try:
        print("🤖 Graph is thinking...")
        final_state = app.invoke(initial_state)
        raw_content = final_state["messages"][-1].content
        
        # FINAL SANITIZATION: Regex finds the first { and last } to ignore "Excellent" chatter
        json_match = re.search(r'(\{.*\})', raw_content, re.DOTALL)
        
        if json_match:
            clean_json = json_match.group(1)
            print(f"✅ CLEANED JSON EXTRACTED")
            return clean_json
        else:
            # If the AI just returned text, wrap it so the UI displays the briefing at least
            print("⚠️ No JSON found, returning text as briefing.")
            return json.dumps({
                "morning_briefing": raw_content,
                "itinerary": []
            })
            
    except Exception as e:
        print(f"❌ GRAPH ERROR: {e}")
        return json.dumps({"status": "error", "message": str(e)})