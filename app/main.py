import sys
import os

# 1. ENSURE PATH IS SET UP CORRECTLY
# Get the project root (parent of 'app' directory)
current_file = os.path.abspath(__file__)
app_dir = os.path.dirname(current_file)  # /path/to/TravellerPie/app
project_root = os.path.dirname(app_dir)  # /path/to/TravellerPie

# Add project root to sys.path so 'app', 'agents', 'tools' modules can be imported
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 2. CLEAN IMPORTS
import json
import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import text
from jose import jwt
from passlib.context import CryptContext

# These will now resolve perfectly because of step 1
from app.database import SessionLocal, User, Itinerary, initialize_database
from agents.orchestrator import run_travel_agents

app = FastAPI()

# Initialize database tables on first use
_db_initialized = False

def ensure_db_initialized():
    global _db_initialized
    if not _db_initialized:
        initialize_database()
        _db_initialized = True

# --- CONFIGURATION ---
SECRET_KEY = os.getenv("JWT_SECRET", "rahul_2026_security_key")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 1. Get the absolute path to the 'app' directory
# Since main.py is in /code/app, this will be /code/app
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Point to the static folder inside 'app'
STATIC_DIR = os.path.join(BASE_DIR, "static")

# 3. Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

def get_db():
    ensure_db_initialized()
    db = SessionLocal()
    try: 
        yield db
    except Exception as e:
        print(f"❌ Database session error: {e}")
        raise
    finally: 
        try:
            db.close()
        except Exception as e:
            print(f"⚠️  Error closing database session: {e}")

# --- ROUTES ---
@app.get("/health")
async def health():
    """Cloud Run health check endpoint."""
    return {"status": "ok"}

@app.get("/")
async def read_index():
    # Points to index.html inside app/templates/
    path = os.path.join(BASE_DIR, "templates", "index.html")
    if not os.path.exists(path):
        return {"error": f"Path not found: {path}"}
    return FileResponse(path)

# app/main.py
@app.post("/register")
async def register(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        # Explicitly pull interests from the JSON body
        new_user = User(
            username=data['username'],
            hashed_password=pwd_context.hash(data['password']),
            interests=data.get('interests', []) # Matches the key from your JS
        )
        db.add(new_user)
        db.commit() # This performs the physical write to Cloud SQL
        return {"status": "success"}
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.username == form_data.username).first()
        if not user or not pwd_context.verify(form_data.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Invalid credentials")
        token = jwt.encode({"sub": user.username}, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/itineraries")
async def get_plans(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = db.query(User).filter(User.username == payload.get("sub")).first()
        if not user: return []
        
        # Fetch plans sorted by newest first
        plans = db.query(Itinerary).filter(Itinerary.user_id == user.id).order_by(Itinerary.created_at.desc()).all()
        return [{"id": p.id, "prompt": p.prompt, "plan": p.plan_data, "date": p.created_at.strftime("%Y-%m-%d")} for p in plans]
    except:
        return []

# Inside app/main.py

@app.post("/generate")
async def generate(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = db.query(User).filter(User.username == payload.get("sub")).first()
        
        if user:
            # 1. CAPTURE NEW INTERESTS FROM UI
            ui_interests = data.get("preferences", [])
            
            # 2. SYNC TO DATABASE
            # We merge current UI tags with existing DB interests
            existing_interests = set(user.interests if user.interests else [])
            updated_interests = list(existing_interests.union(set(ui_interests)))
            
            if updated_interests != user.interests:
                user.interests = updated_interests
                db.commit() # This physically writes to Cloud SQL
                print(f"DEBUG: Synchronized {len(updated_interests)} interests for {user.username}")

            # 3. ENSURE ORCHESTRATOR USES THESE
            data["preferences"] = updated_interests
            
    except Exception as e:
        print(f"DEBUG: Auth/Sync Error: {e}")

    # 4. RUN AGENTS & PERSIST ITINERARY
    result_str = await run_travel_agents(data)
    result_json = json.loads(result_str)

    if user:
        db.add(Itinerary(user_id=user.id, prompt=data.get("prompt"), plan_data=result_json))
        db.commit()

    return result_json

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)