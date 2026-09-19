import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Ensure static uploads folder exists
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "campuscare-production-secret-2026-key")
    
    # Handle Render's DATABASE_URL which might start with postgres:// instead of postgresql://
    raw_db_url = os.environ.get("DATABASE_URL")
    if raw_db_url and raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = raw_db_url or f"sqlite:///{os.path.join(DATA_DIR, 'campuscare.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
    AUTO_ASSIGN_THRESHOLD = int(os.environ.get("AUTO_ASSIGN_THRESHOLD", 60))


