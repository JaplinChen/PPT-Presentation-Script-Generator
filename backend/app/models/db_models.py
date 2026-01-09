from sqlalchemy import Column, String, Integer, JSON, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import datetime
from pathlib import Path

# Database setup
DB_FILE = Path("data.db")
DATABASE_URL = f"sqlite:///./{DB_FILE}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()

class FileRecord(Base):
    __tablename__ = "files"
    
    file_id = Column(String, primary_key=True, index=True)
    filename = Column(String)
    path = Column(String)
    status = Column(String)
    slides = Column(JSON, default=list)
    summary = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ParseStatusRecord(Base):
    __tablename__ = "parse_status"
    
    file_id = Column(String, primary_key=True, index=True)
    status = Column(String)
    progress = Column(Integer, default=0)
    message = Column(String)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class JobRecord(Base):
    __tablename__ = "jobs"
    
    job_id = Column(String, primary_key=True, index=True)
    file_id = Column(String, index=True)
    job_type = Column(String) # 'narrated', 'assemble'
    status = Column(String)
    progress = Column(Integer, default=0)
    message = Column(String)
    result = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class CacheRecord(Base):
    __tablename__ = "generation_cache"
    
    cache_key = Column(String, primary_key=True, index=True) # e.g. "file_id|prompt_hash"
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
