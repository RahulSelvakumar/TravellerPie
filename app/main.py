import os
import sys
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from fastapi.staticfiles import StaticFiles


# Ensure the root directory is in the path for internal imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.orchestrator import run_travel_agents

app = FastAPI()
# 1. DEFINE base_dir FIRST
base_dir = os.path.dirname(os.path.abspath(__file__))

# 2. NOW you can use it for templates and static files
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")

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
async def generate(request: Request):
    try:
        # 1. Parse the incoming JSON request
        data = await request.json()
        user_prompt = data.get("prompt", "Plan a luxury trip")
        user_prefs = data.get("preferences", [])

        # 2. DEFINE initial_state (This is what was missing!)
        initial_state = {
            "messages": [HumanMessage(content=user_prompt)],
            "preferences": user_prefs
        }
        
        # 3. Now call the graph
        result_string = run_travel_agents(initial_state)
        
        # 4. Convert and return
        if isinstance(result_string, str):
            result_data = json.loads(result_string)
        else:
            result_data = result_string

        return JSONResponse(content=result_data)
        
    except Exception as e:
        print(f"❌ Route Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

    
if __name__ == "__main__":
    import uvicorn
    # Cloud Run injects "PORT". If it's missing (local), use 8080.
    port = int(os.environ.get("PORT", 8080)) 
    uvicorn.run(app, host="0.0.0.0", port=port)