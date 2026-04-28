import os
import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Load environment variables from .env when present
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = f"sqlite:///{os.path.join(os.getcwd(), 'travellerpie.db')}"
    print("WARNING: DATABASE_URL not set; falling back to local SQLite database.")

# MySQL Engine Configuration
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True, 
    pool_recycle=3600
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    # MySQL requires lengths for indexed VARCHAR columns
    username = Column(String(150), unique=True, index=True)
    hashed_password = Column(String(255))
    interests = Column(JSON, default=[]) 
    itineraries = relationship("Itinerary", back_populates="owner")

class Itinerary(Base):
    __tablename__ = "itineraries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    prompt = Column(String(500))
    plan_data = Column(JSON) 
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    owner = relationship("User", back_populates="itineraries")

# Initialize tables in Cloud SQL
Base.metadata.create_all(bind=engine)