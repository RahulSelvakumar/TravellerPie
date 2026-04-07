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
    # This explicit keyword format prevents the 'unhashable type' error
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request}
    )
# --- MERGED GENERATE ROUTE ---
import json
from fastapi.responses import JSONResponse

@app.post("/generate")
async def generate_itinerary(request: Request):
    try:
        data = await request.json()
        user_prompt = data.get("prompt", "Plan a trip")
        user_prefs = data.get("preferences", [])

        initial_state = {
            "messages": [HumanMessage(content=user_prompt)],
            "preferences": user_prefs
        }
        
        # This returns a STRING (e.g., '{"morning_briefing": "..."}')
        result_string = run_travel_agents(initial_state)
        
        # CRITICAL FIX: Convert the string back to a Python Dict 
        # so FastAPI can send it as valid JSON
        result_dict = json.loads(result_string)
        return JSONResponse(content=result_dict)
        
    except Exception as e:
        # This will now print the EXACT error in your Cloud Run logs
        print(f"❌ CRITICAL ERROR IN ROUTE: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})
    
if __name__ == "__main__":
    import uvicorn
    # Cloud Run injects "PORT". If it's missing (local), use 8080.
    port = int(os.environ.get("PORT", 8080)) 
    uvicorn.run(app, host="0.0.0.0", port=port)