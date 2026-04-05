import json
import operator
from typing import Annotated, List, TypedDict, Union
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from .sub_agents import TravellerSubAgents

# --- 1. State Definition ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    next: str

# --- 2. Setup ---
sub_agents = TravellerSubAgents()
supervisor_llm = ChatVertexAI(model_name="gemini-1.5-pro-preview-0409", temperature=0)

# --- 3. Node Functions ---
def call_transit(state: AgentState):
    response = sub_agents.transit_agent(state['messages'])
    return {"messages": [HumanMessage(content=response.content, name="TransitAgent")]}

def call_intel(state: AgentState):
    response = sub_agents.intel_agent(state['messages'])
    return {"messages": [HumanMessage(content=response.content, name="LocalIntelAgent")]}

def call_planning(state: AgentState):
    response = sub_agents.planning_agent(state['messages'])
    return {"messages": [HumanMessage(content=response.content, name="PlanningAgent")]}

def supervisor_node(state: AgentState):
    members = ["TransitAgent", "LocalIntelAgent", "PlanningAgent"]
    system_prompt = (
        "You are the TravellerPie Supervisor. Route the request to the correct agent. "
        "When the plan is ready, output the final result in STRICT RAW JSON. "
        "SCHEMA: {{\"status\": \"success\", \"morning_briefing\": \"str\", \"itinerary\": [{{ \"time\": \"str\", \"event\": \"str\", \"type\": \"str\" }}]}}"
    )
    prompt = [SystemMessage(content=system_prompt)] + state['messages']
    response = supervisor_llm.invoke(prompt)
    
    # Logic to decide next step
    if "itinerary" in response.content.lower():
        return {"next": END, "messages": [response]}
    
    # Simple keyword routing for the hackathon
    content = response.content.upper()
    if "TRANSIT" in content: return {"next": "TransitAgent"}
    if "INTEL" in content: return {"next": "LocalIntelAgent"}
    return {"next": "PlanningAgent"}

# --- 4. Graph Construction ---
workflow = StateGraph(AgentState)
workflow.add_node("TransitAgent", call_transit)
workflow.add_node("LocalIntelAgent", call_intel)
workflow.add_node("PlanningAgent", call_planning)
workflow.add_node("Supervisor", supervisor_node)

workflow.add_edge("TransitAgent", "Supervisor")
workflow.add_edge("LocalIntelAgent", "Supervisor")
workflow.add_edge("PlanningAgent", "Supervisor")

workflow.add_conditional_edges("Supervisor", lambda x: x["next"], {
    "TransitAgent": "TransitAgent",
    "LocalIntelAgent": "LocalIntelAgent",
    "PlanningAgent": "PlanningAgent",
    END: END
})

workflow.set_entry_point("Supervisor")
graph = workflow.compile()

def run_travel_agents(user_prompt: str):
    inputs = {"messages": [HumanMessage(content=user_prompt)]}
    final_state = graph.invoke(inputs)
    raw_res = final_state['messages'][-1].content
    return json.loads(raw_res.replace("```json", "").replace("```", ""))