import os
import sys
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

# Ensure the root directory is in the path for internal imports
# This is critical for Cloud Run to see 'agents' and 'tools'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.orchestrator import run_travel_agents

app = FastAPI()

# Absolute pathing for templates ensures reliability in Linux containers
base_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

class TravelRequest(BaseModel):
    prompt: str
    preferences: list = []

@app.get("/health")
async def health_check():
    return {"status": "online", "version": "1.0.1"}

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate_itinerary(request: Request):
    try:
        data = await request.json()
        user_prompt = str(data.get("prompt", "Plan a trip"))
        user_prefs = data.get("preferences", []) 
        
        print(f"🚀 Launching Agents for: {user_prompt}")

        initial_state = {
            "messages": [HumanMessage(content=user_prompt)],
            "preferences": user_prefs
        }
        
        # run_travel_agents returns a JSON STRING based on your orchestrator.py
        result_string = run_travel_agents(initial_state)
        
        # We manually parse the string back to a dict to ensure 
        # FastAPI sends a valid application/json response
        return JSONResponse(content=json.loads(result_string))
        
    except Exception as e:
        print(f"❌ Execution Error: {e}")
        return JSONResponse(
            status_code=500, 
            content={"status": "error", "message": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    # Cloud Run requirement: Listen on the PORT provided by the environment
    port = int(os.environ.get("PORT", 8080)) 
    uvicorn.run(app, host="0.0.0.0", port=port)