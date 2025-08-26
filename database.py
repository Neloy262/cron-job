import urllib.parse
import uuid
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from decouple import Config, RepositoryEnv
import os

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
config = Config(RepositoryEnv(env_path))

# Database configuration
DB_HOST = config('DB_HOST')
DB_PORT = config('DB_PORT')
DB_NAME = config('DB_NAME')
DB_USER = config('DB_USER')
DB_PASSWORD = config('DB_PASSWORD')

# URL encode the password to handle special characters
DB_PASSWORD_ENCODED = urllib.parse.quote_plus(DB_PASSWORD)

# Create the database connection string for SQL Server
DATABASE_URL = f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}?driver=ODBC+Driver+17+for+SQL+Server"

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# CronJobs model
class CronJob(Base):
    __tablename__ = "CronJobs"
    
    Id = Column(Integer, primary_key=True, autoincrement=True)
    JobType = Column(String(100), nullable=False)
    JobId = Column(String(100), nullable=True)
    Schedule = Column(String(100), nullable=False)
    Status = Column(Boolean, default=True, nullable=False)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # We'll close the session in the calling function

def create_cron_job(job_type: str, schedule: str, job_id: str = None):
    """Create a new cron job record in the database"""
    db = get_db()
    try:
        # If no job_id provided, generate one
        if job_id is None:
            job_id = str(uuid.uuid4())
        
        db_cron_job = CronJob(JobType=job_type, JobId=job_id, Schedule=schedule, Status=True)
        db.add(db_cron_job)
        db.commit()
        db.refresh(db_cron_job)
        return db_cron_job
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def update_cron_job(job_type: str, new_schedule: str, job_id: str = None):
    """Update an existing cron job record in the database"""
    db = get_db()
    try:
        if job_id:
            # Update specific job by job_id
            db_cron_job = db.query(CronJob).filter(CronJob.JobType == job_type, CronJob.JobId == job_id, CronJob.Status == True).first()
        else:
            # Update by job_type only (backward compatibility)
            db_cron_job = db.query(CronJob).filter(CronJob.JobType == job_type, CronJob.Status == True).first()
        
        if db_cron_job:
            db_cron_job.Schedule = new_schedule
            db.commit()
            db.refresh(db_cron_job)
            return db_cron_job
        return None
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def delete_cron_job(job_type: str, job_id: str = None):
    """Mark a cron job as deleted (set Status to False) in the database"""
    db = get_db()
    try:
        if job_id:
            # Delete specific job by job_id
            db_cron_job = db.query(CronJob).filter(CronJob.JobType == job_type, CronJob.JobId == job_id, CronJob.Status == True).first()
        else:
            # Delete by job_type only (backward compatibility)
            db_cron_job = db.query(CronJob).filter(CronJob.JobType == job_type, CronJob.Status == True).first()
        
        if db_cron_job:
            db_cron_job.Status = False
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_cron_job(job_type: str, job_id: str = None):
    """Get a specific cron job from the database"""
    db = get_db()
    try:
        if job_id:
            # Get specific job by job_id
            return db.query(CronJob).filter(CronJob.JobType == job_type, CronJob.JobId == job_id, CronJob.Status == True).first()
        else:
            # Get by job_type only
            return db.query(CronJob).filter(CronJob.JobType == job_type, CronJob.Status == True).first()
    finally:
        db.close()