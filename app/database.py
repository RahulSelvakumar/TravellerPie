import os
import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, JSON, ForeignKey, DateTime, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import NullPool, QueuePool

# Load environment variables from .env when present
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = f"sqlite:///{os.path.join(os.getcwd(), 'travellerpie.db')}"
    print("WARNING: DATABASE_URL not set; falling back to local SQLite database.")

# MySQL Engine Configuration
# For Cloud SQL public IP connections, disable SSL verification
connect_args = {}
pool_class = QueuePool
pool_kwargs = {
    "pool_size": 5,
    "max_overflow": 10,
    "pool_recycle": 1800,
}

# Auto-detect Cloud Run environment
is_cloud_run = os.getenv("K_SERVICE") is not None or os.getenv("ENVIRONMENT") == "cloud"

if "pymysql" in DATABASE_URL:
    connect_args = {
        "ssl_verify_cert": False,
        "ssl_verify_identity": False,
        "charset": "utf8mb4",
        "read_timeout": 60,
        "write_timeout": 60,
        "connect_timeout": 10
    }
    # Use NullPool for serverless/container environments to avoid stale connections
    if is_cloud_run:
        pool_class = NullPool
        pool_kwargs = {}  # NullPool doesn't accept pool_size or max_overflow
        print("ℹ️  Running in Cloud Run - using NullPool for database connections")

engine = create_engine(
    DATABASE_URL, 
    connect_args=connect_args,
    poolclass=pool_class,
    pool_pre_ping=True,
    echo=False,
    **pool_kwargs
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

# Initialize tables in Cloud SQL (lazy - will run on first DB access)
def initialize_database():
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables initialized successfully")
    except Exception as e:
        print(f"⚠️  Database initialization error: {e}")

# Don't initialize on import - lazy initialization instead
