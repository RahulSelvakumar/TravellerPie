import os
import sys
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates # The fix
from langchain_core.messages import HumanMessage

# Critical path fix
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.orchestrator import run_travel_agents

app = FastAPI()

# Setup paths
base_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate(request: Request):
    try:
        data = await request.json()
        initial_state = {
            "messages": [HumanMessage(content=data.get("prompt"))],
            "preferences": data.get("preferences", []),
            "next": ""
        }
        result_json = await run_travel_agents(initial_state)
        return JSONResponse(content=json.loads(result_json))
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)