from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from utils import get_secret
import os

# Build DB URL
POSTGRES_USER = get_secret("postgres_user", "postgres")
POSTGRES_PASSWORD = get_secret("postgres_password", "password")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "pdfsimple")
POSTGRES_HOST = "postgres"
POSTGRES_PORT = "5432"

SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
