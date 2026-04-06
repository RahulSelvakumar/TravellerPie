# app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
# --- ADD THESE IMPORTS ---
from langchain_core.messages import HumanMessage 
from agents.orchestrator import run_travel_agents
# -------------------------

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# ... (rest of your code)

class TravelRequest(BaseModel):
    prompt: str

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate_itinerary(request: Request):
    data = await request.json()
    user_prompt = data.get("prompt")
    
    # FIX: Extract preferences from the incoming JSON
    # If the UI doesn't send them, we default to an empty list []
    user_preferences = data.get("preferences", []) 
    
    try:
        # Pass the preferences into the orchestrator
        result = run_travel_agents({
            "messages": [HumanMessage(content=user_prompt)],
            "preferences": user_preferences # <--- THIS MUST BE HERE
        })
        return result
    except Exception as e:
        print(f"Agent Error: {e}")
        return {"status": "error", "message": str(e)}
    
@app.post("/generate")
async def generate_itinerary(request: Request):
    # 1. Parse the JSON from the UI
    data = await request.json()
    
    # 2. Extract the string and the list
    user_prompt = str(data.get("prompt", "Plan a trip"))
    user_prefs = data.get("preferences", []) # This is already a list
    
    # 3. CONSTRUCT THE STATE MANUALLY
    # LangGraph state needs 'messages' to be a LIST
    initial_state = {
        "messages": [HumanMessage(content=user_prompt)],
        "preferences": user_prefs
    }
    
    try:
        print(f"🚀 Launching Agents for: {user_prompt}")
        
        # 4. Pass the dictionary directly
        # DO NOT wrap it in another dict like: run_travel_agents({"state": initial_state})
        result = run_travel_agents(initial_state)
        
        return result
        
    except Exception as e:
        print(f"❌ Execution Error: {e}")
        return {"status": "error", "message": str(e)}