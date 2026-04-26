import json, operator, re, os, asyncio
from typing import Annotated, List, TypedDict, Sequence
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
import json, re, operator

# 1. State Definition
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    preferences: List[str]
    next: str

# 2. Model Initialization
llm = ChatVertexAI(
    model_name="gemini-2.5-flash", 
    project="travellerpie-hackathon", 
    location="us-central1"
)

# 3. Supervisor Node - Flexible for any number of days
async def supervisor_node(state: AgentState):
    # EXTRACTION: Manually find the number of days in the prompt
    user_text = state['messages'][-1].content
    day_match = re.search(r'(\d+)\s*day', user_text, re.IGNORECASE)
    num_days = day_match.group(1) if day_match else "5" # Default to 5 if not found

    system_prompt = f"""You are the TravellerPie Lead. You MUST return ONLY a JSON object. 
    The user is traveling for EXACTLY {num_days} days. Generate a JSON object with {num_days} entries in the 'days' array.
    
    CRITICAL: Do not ask questions. Do not use markdown backticks. 
    Return ONLY the raw JSON string matching this schema:
    {{
      "morning_briefing": "...",
      "logistics": {{ "flight_path": "...", "airline": "...", "departure": "...", "arrival": "..." }},
      "days": [ {{ "day_number": 1, "hotel": "...", "morning": "...", "afternoon": "...", "evening": "...", "snack": "..." }} ],
      "sources": []
    }}"""

    response = await llm.ainvoke([SystemMessage(content=system_prompt)] + state['messages'])
    return {"next": END, "messages": [response]}

# 4. Graph Assembly
workflow = StateGraph(AgentState)
workflow.add_node("Supervisor", supervisor_node)
workflow.set_entry_point("Supervisor")
app = workflow.compile() # Compiled as 'app'

# 5. Main Execution Function
async def run_travel_agents(initial_state: dict):
    # Ensure initial_state contains 'prompt'
    prompt_text = initial_state.get("prompt", "Japan trip")
    prefs = initial_state.get("preferences", [])
    
    inputs = {
        "messages": [HumanMessage(content=prompt_text)],
        "preferences": prefs
    }
    
    try:
        final_state = await app.ainvoke(inputs, {"recursion_limit": 50})
        content = final_state["messages"][-1].content
        
        # Regex to strip markdown and extract JSON
        match = re.search(r'(\{.*\})', content, re.DOTALL)
        json_string = match.group(1) if match else content
        
        print(f"\n🚀 [DEBUG] SUCCESSFUL ORCHESTRATION:\n{json_string[:200]}...")
        return json_string
    except Exception as e:
        print(f"❌ [DEBUG] ERROR: {str(e)}")
        return json.dumps({"error": str(e), "morning_briefing": "System handshake error."})