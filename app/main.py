# app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from tools.weather_api import get_current_weather

app = FastAPI(title="TravellerPie")

# Tell FastAPI where to find your new HTML file
templates = Jinja2Templates(directory="app/templates")

# This defines what data the frontend will send us
class TravelRequest(BaseModel):
    prompt: str

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    # This serves your beautiful Tailwind UI!
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate_itinerary(req: TravelRequest):
    # Let's call your actual weather tool! 
    # We will hardcode "Bengaluru" for this test, but the AI will choose the city dynamically tomorrow.
    real_weather = get_current_weather("Bengaluru")

    mock_result = {
        "status": "success",
        "morning_briefing": f"Received your request: '{req.prompt}'. {real_weather}. Running multi-agent triage...",
        "itinerary": [
            {"time": "09:00 AM", "event": "Breakfast at local cafe"},
            {"time": "10:30 AM", "event": "Visit National Indoor Museum"},
            {"time": "01:00 PM", "event": "Lunch at Ramen Street"}
        ]
    }
    return mock_result

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "TravellerPie Core"}