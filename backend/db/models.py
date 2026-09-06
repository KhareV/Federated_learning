from sqlalchemy import Column, Integer, String, Float, JSON, DateTime
from backend.db.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    role = Column(String)

class SystemEvent(Base):
    __tablename__ = "system_events"
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String)
    source = Column(String)
    message = Column(String)
    extra_data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)