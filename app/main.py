import sys
import os
import json
import hashlib
import uvicorn

# 1. ENSURE MODULE RESOLUTION
# Added to make sure 'app', 'agents', and 'tools' are discoverable in Cloud Run
current_file = os.path.abspath(__file__)
app_dir = os.path.dirname(current_file)
project_root = os.path.dirname(app_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from jose import jwt

# Internal project imports
from app.database import SessionLocal, User, Itinerary, initialize_database
from agents.orchestrator import run_travel_agents

app = FastAPI(title="TravellerPie Global Orchestrator")

# 2. CORS MIDDLEWARE
# Essential for preventing "Handshake Errors" when frontend and backend communicate via Cloud Run URLs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. DATABASE INITIALIZATION
_db_initialized = False

def ensure_db_initialized():
    global _db_initialized
    if not _db_initialized:
        initialize_database()
        _db_initialized = True

def get_db():
    ensure_db_initialized()
    db = SessionLocal()
    try: 
        yield db
    except Exception as e:
        print(f"❌ Database session error: {e}")
        raise
    finally: 
        db.close()

def get_password_hash(password: str) -> str:
    """Hash password with PBKDF2-SHA256 + random salt (stdlib only, no bcrypt)."""
    import secrets
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000).hex()
    return f"{salt}:{hashed}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify against PBKDF2-SHA256 hash."""
    try:
        salt, stored_hash = hashed_password.split(":", 1)
        candidate = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt.encode(), 260000).hex()
        return candidate == stored_hash
    except Exception:
        return False

# 4. SECURITY CONFIGURATION
SECRET_KEY = os.getenv("JWT_SECRET", "rahul_2026_security_key")
ALGORITHM = "HS256"

# 5. STATIC ASSET MAPPING
# Uses absolute pathing to ensure the logo is found in the 'app/static' directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --- ROUTES ---

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def read_index():
    path = os.path.join(BASE_DIR, "templates", "index.html")
    if not os.path.exists(path):
        return {"error": "Index template missing"}
    return FileResponse(path)

@app.post("/register")
async def register(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        new_user = User(
            username=data['username'],
            hashed_password=get_password_hash(data['password']), 
            interests=data.get('interests', [])
        )
        db.add(new_user)
        db.commit()
        return {"status": "success"}
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.username == form_data.username).first()
        
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Invalid credentials")
            
        token = jwt.encode({"sub": user.username}, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        print(f"❌ Login Handshake Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Identity verification failed")

@app.get("/itineraries")
async def get_plans(request: Request, db: Session = Depends(get_db)):
    # Logic to fetch archived plans from Cloud SQL
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = db.query(User).filter(User.username == payload.get("sub")).first()
        if not user: return []
        
        plans = db.query(Itinerary).filter(Itinerary.user_id == user.id).order_by(Itinerary.created_at.desc()).all()
        return [{"id": p.id, "prompt": p.prompt, "plan": p.plan_data, "date": p.created_at.strftime("%Y-%m-%d")} for p in plans]
    except Exception as e:
        return []

@app.post("/generate")
async def generate(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = db.query(User).filter(User.username == payload.get("sub")).first()
        
        if user:
            # Synchronize UI context engine tags with Cloud SQL profile
            ui_interests = data.get("preferences", [])
            existing_interests = set(user.interests if user.interests else [])
            updated_interests = list(existing_interests.union(set(ui_interests)))
            
            if updated_interests != user.interests:
                user.interests = updated_interests
                db.commit()
            
            data["preferences"] = updated_interests
            
    except Exception as e:
        print(f"DEBUG: Auth/Sync Error: {e}")

    # Invoke Multi-Agent Triage
    result_str = await run_travel_agents(data)
    result_json = json.loads(result_str)

    if user:
        db.add(Itinerary(user_id=user.id, prompt=data.get("prompt"), plan_data=result_json))
        db.commit()

    return result_json

@app.post("/cron/sync-disruptions")
async def handle_cron_check(request: Request):
    # Security: Cloud Scheduler sends an OIDC token in the header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # In a real app, you'd iterate through all active trips
        # For the hackathon demo, we trigger it for your test user
        from agents.orchestrator import run_disruption_update
        await run_disruption_update(user_id="RUPASH8754", plan_id=1)
        
        return {"status": "success", "message": "5AM Disruption check complete."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Local dev entry point
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)