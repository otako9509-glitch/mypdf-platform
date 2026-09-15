from sqlalchemy import Column, String, DateTime, Text, Integer, Enum as SQLEnum
from sqlalchemy.sql import func
from database import Base
import enum


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, index=True)
    operation = Column(String, nullable=False, index=True)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    input_files = Column(Text, nullable=False)  # JSON string
    output_file = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    progress = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "operation": self.operation,
            "status": self.status.value if isinstance(self.status, JobStatus) else self.status,
            "input_files": self.input_files,
            "output_file": self.output_file,
            "error": self.error,
            "progress": self.progress,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
