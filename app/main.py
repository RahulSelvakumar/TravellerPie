import os
import sys
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

# Ensure the root directory is in the path for internal imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.orchestrator import run_travel_agents

app = FastAPI()

# Cloud Run health check requires a reliable path to templates
# Using absolute pathing ensures Jinja2 finds the folder regardless of WORKDIR
base_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

class TravelRequest(BaseModel):
    prompt: str
    preferences: list = []

# --- HEALTH CHECK (Mandatory for Cloud Run) ---
@app.get("/health")
async def health_check():
    return {"status": "online", "version": "1.0.0"}

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- MERGED GENERATE ROUTE ---
@app.post("/generate")
async def generate_itinerary(request: Request):
    try:
        # 1. Parse the JSON from the UI
        data = await request.json()
        
        # 2. Extract the string and the list with safe defaults
        user_prompt = str(data.get("prompt", "Plan a trip"))
        user_prefs = data.get("preferences", []) 
        
        print(f"🚀 Launching Agents for: {user_prompt}")
        print(f"Context Engine Tags: {user_prefs}")

        # 3. Construct the state for LangGraph
        # 'messages' must be a list of BaseMessages
        initial_state = {
            "messages": [HumanMessage(content=user_prompt)],
            "preferences": user_prefs
        }
        
        # 4. Invoke the Orchestrator
        # The result returned here is the JSON string from run_travel_agents
        result = run_travel_agents(initial_state)
        
        # FastAPI will automatically set content-type to application/json 
        # if 'result' is a dict or a valid JSON string
        return result
        
    except Exception as e:
        print(f"❌ Execution Error: {e}")
        return {"status": "error", "message": str(e)}

# --- UVICORN STARTUP ---
if __name__ == "__main__":
    import uvicorn
    # Use PORT from environment (Cloud Run requirement)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)