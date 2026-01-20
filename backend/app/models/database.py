"""
Database Models - UPDATED VERSION
Exports the fixed save function with deduplication logic and Connection Pooling fixes
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Boolean, select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid

from app.core.config import settings


# Create base class for models
Base = declarative_base()


# ============================================================================
# DATABASE ENGINE (FIXED STABILITY)
# ============================================================================

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False, # Set to False in production to reduce log noise
    future=True,
    # --- STABILITY FIXES ---
    pool_pre_ping=True,      # Checks if connection is alive before using (Fixes InterfaceError)
    pool_size=20,            # Increase pool size for frontend polling
    max_overflow=10,         # Allow temporary spikes
    pool_recycle=1800        # Recycle connections every 30 mins
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# ============================================================================
# MODELS
# ============================================================================

class User(Base):
    """User table"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=True)
    github_username = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Repository(Base):
    """Repository analysis results"""
    __tablename__ = "repositories"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Basic info
    repo_url = Column(String, nullable=False, index=True)
    repo_fingerprint = Column(String, unique=True, index=True) # Used for Commit Hash
    owner = Column(String, nullable=False)
    name = Column(String, nullable=False)
    
    # User
    user_id = Column(String, nullable=True)
    
    # Results
    final_credits = Column(Float, nullable=True, default=0.0)
    sfia_level = Column(Integer, nullable=True)
    
    # Full state (stored as JSON)
    validation_result = Column(JSON, nullable=True)
    scan_metrics = Column(JSON, nullable=True)
    sfia_result = Column(JSON, nullable=True)
    audit_result = Column(JSON, nullable=True)
    
    # Observability
    opik_trace_id = Column(String, nullable=True)
    errors = Column(JSON, default=list)
    
    # Timestamps
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CreditLedger(Base):
    """Immutable audit trail of credits"""
    __tablename__ = "credit_ledger"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    user_id = Column(String, nullable=False, index=True)
    repo_id = Column(String, nullable=False)
    credits_awarded = Column(Float, nullable=False)
    audit_trail = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AnalysisJob(Base):
    """Tracks running/completed jobs"""
    __tablename__ = "analysis_jobs"
    
    job_id = Column(String, primary_key=True)
    repo_url = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    
    status = Column(String, default="queued")
    current_step = Column(String, nullable=True)
    progress = Column(Integer, default=0)
    result = Column(JSON, nullable=True)
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

async def init_db():
    """Create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created")


async def get_db():
    """Dependency for FastAPI routes"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ============================================================================
# IMPORT THE FIXED SAVE FUNCTION
# ============================================================================

async def save_analysis_result(state: dict):
    """
    Save analysis result to database (FIXED - HANDLES ALL NONE VALUES & DEDUPLICATION)
    """
    
    async with async_session() as session:
        try:
            # Extract data with safe defaults
            repo_url = state.get("repo_url", "Unknown")
            user_id = state.get("user_id", "anonymous")
            job_id = state.get("job_id", "unknown")
            
            validation = state.get("validation") or {}
            owner = validation.get("owner", "unknown")
            repo_name = validation.get("repo_name", "unknown")
            
            final_credits = state.get("final_credits", 0.0)
            
            sfia_result = state.get("sfia_result") or {}
            sfia_level = sfia_result.get("sfia_level")
            
            errors = state.get("errors", [])
            
            # --- DEDUPLICATION CHECK ---
            # 1. Get the Commit Hash (stored in repo_fingerprint in scanner)
            scan_metrics = state.get("scan_metrics") or {}
            ncrf_data = scan_metrics.get("ncrf") or {}
            commit_hash = ncrf_data.get("repo_fingerprint", job_id) # Fallback to job_id if no hash

            # 2. Check if we have already awarded credits for THIS specific commit
            # We look for a repository record with the same fingerprint and > 0 credits
            prev_run_query = await session.execute(
                select(Repository)
                .where(Repository.user_id == user_id)
                .where(Repository.repo_url == repo_url)
                .where(Repository.repo_fingerprint == commit_hash)
                .where(Repository.final_credits > 0)
            )
            existing_reward = prev_run_query.scalars().first()
            
            # Determine if we should award new credits
            should_award_credits = False
            credits_to_record = final_credits

            if final_credits > 0:
                if existing_reward:
                    print(f"⚠️ User {user_id} already rewarded for commit {commit_hash[:7]}. Marking as duplicate.")
                    credits_to_record = 0.0 # Zero out credits for duplicate run
                else:
                    print(f"✅ New version detected ({commit_hash[:7]}). Awarding credits.")
                    should_award_credits = True

            # Create repository record (We always save the run history)
            repo = Repository(
                repo_url=repo_url,
                repo_fingerprint=commit_hash, # Save the actual commit hash
                owner=owner,
                name=repo_name,
                user_id=user_id,
                final_credits=credits_to_record, # Uses 0.0 if duplicate
                sfia_level=sfia_level,
                validation_result=validation if validation else None,
                scan_metrics=state.get("scan_metrics"),
                sfia_result=sfia_result if sfia_result else None,
                audit_result=state.get("audit_result"),
                opik_trace_id=state.get("opik_trace_id"),
                errors=errors
            )
            
            session.add(repo)
            await session.commit()
            
            print(f"✅ Database: Saved repository record ({repo.id})")
            
            # Create credit ledger entry ONLY if it's a new, valid reward
            if should_award_credits:
                ledger_entry = CreditLedger(
                    user_id=user_id,
                    repo_id=repo.id,
                    credits_awarded=final_credits,
                    audit_trail=state
                )
                
                session.add(ledger_entry)
                await session.commit()
                
                print(f"✅ Database: Saved credit ledger entry")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Database save failed: {str(e)}")
            # Don't re-raise, allow the app to continue reporting the error
            pass 


async def get_user_total_credits(user_id: str) -> float:
    """Get total credits for a user"""
    async with async_session() as session:
        result = await session.execute(
            select(func.sum(CreditLedger.credits_awarded))
            .where(CreditLedger.user_id == user_id)
        )
        total = result.scalar()
        return total or 0.0