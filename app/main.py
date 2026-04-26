from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import sys
import json

# 1. FIX PATHS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 2. IMPORT LOGIC
from agents.orchestrator import run_travel_agents

# 3. INIT APP
app = FastAPI()

# 4. CONFIGURE DIRS (Using the 'app/' prefix as per your project structure)
templates = Jinja2Templates(directory="app/templates")

if os.path.exists("app/static"):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html", context={})

@app.post("/generate")
async def generate(request: Request):
    try:
        data = await request.json()
        result_json = await run_travel_agents(data)
        # Convert string response to JSON object for FastAPI
        return json.loads(result_json)
    except Exception as e:
        print(f"❌ ROUTE ERROR: {str(e)}")
        return {"morning_briefing": f"Error: {str(e)}", "days": [], "logistics": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)