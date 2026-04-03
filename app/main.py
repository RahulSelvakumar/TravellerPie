from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="TravellerPie API")

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>TravellerPie</title>
            <style>
                body { font-family: sans-serif; text-align: center; margin-top: 50px; background-color: #f9f9f9; }
                h1 { color: #333; }
                p { color: #666; }
            </style>
        </head>
        <body>
            <h1>Welcome to TravellerPie 🥧</h1>
            <p>Your Hyper-Dynamic Travel & Logistics Orchestrator is online!</p>
            <p><strong>System Status:</strong> Awaiting Vertex AI Orchestrator connection...</p>
        </body>
    </html>
    """

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "TravellerPie Core"}