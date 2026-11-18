from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from pathlib import Path
import os
from src.utils.config import get_app_config as load_config

Base = declarative_base()


class InspectionRecord(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(String(36), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    image_shape = Column(String(50))
    defects_count = Column(Integer, default=0)
    decision = Column(String(10))
    processing_time_ms = Column(Float)
    result_json = Column(Text)


def get_database_url() -> str:
    config = load_config()
    db_config = config.get("database", {})
    host = db_config.get("host", os.getenv("DB_HOST", "localhost"))
    port = db_config.get("port", os.getenv("DB_PORT", "5432"))
    name = db_config.get("name", os.getenv("DB_NAME", "inspection"))
    user = db_config.get("user", os.getenv("DB_USER", "postgres"))
    password = db_config.get("password", os.getenv("DB_PASSWORD", "postgres"))

    if os.getenv("USE_SQLITE", "true").lower() == "true":
        db_path = Path("experiments/inspection.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"

    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


engine = create_engine(get_database_url(), echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()