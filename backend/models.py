from sqlalchemy import Column, Integer, String, BigInteger, DateTime
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    # Quota in bytes. Default 100MB.
    quota_bytes = Column(BigInteger, default=100 * 1024 * 1024) 
    usage_bytes = Column(BigInteger, default=0)

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)
    status = Column(String)
    tool = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
