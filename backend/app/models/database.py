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
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
    pool_recycle=1800
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
    repo_fingerprint = Column(String, unique=True, index=True)
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
    validation_metrics = Column(JSON, nullable=True)
    quality_metrics = Column(JSON, nullable=True)
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
# FIXED SAVE FUNCTION
# ============================================================================

async def save_analysis_result(state: dict):
    """
    FIXED: Properly handles duplicates by UPDATING instead of INSERT
    """
    
    async with async_session() as session:
        try:
            # Extract data
            repo_url = state.get("repo_url", "Unknown")
            user_id = state.get("user_id", "anonymous")
            
            validation = state.get("validation") or {}
            owner = validation.get("owner", "unknown")
            repo_name = validation.get("repo_name", "unknown")
            
            final_credits = state.get("final_credits", 0.0)
            sfia_result = state.get("sfia_result") or {}
            sfia_level = sfia_result.get("sfia_level")
            
            # Get commit hash
            scan_metrics = state.get("scan_metrics") or {}
            ncrf_data = scan_metrics.get("ncrf") or {}
            commit_hash = ncrf_data.get("repo_fingerprint", state.get("job_id"))

            # --- DEDUPLICATION CHECK ---
            # Check if this EXACT commit has already been rewarded
            existing = await session.execute(
                select(Repository)
                .where(Repository.repo_fingerprint == commit_hash)
                .where(Repository.user_id == user_id)
            )
            existing_record = existing.scalars().first()
            
            if existing_record:
                print(f"⚠️ Duplicate detected for commit {commit_hash[:7]}. Updating record instead of inserting.")
                
                # UPDATE the existing record instead of failing
                existing_record.validation_result = validation if validation else None
                existing_record.scan_metrics = state.get("scan_metrics")
                existing_record.sfia_result = sfia_result if sfia_result else None
                existing_record.audit_result = state.get("audit_result")
                existing_record.opik_trace_id = state.get("opik_trace_id")
                existing_record.errors = state.get("errors", [])
                existing_record.updated_at = datetime.utcnow()
                
                # DON'T change final_credits if already awarded
                if existing_record.final_credits == 0.0 and final_credits > 0:
                    print(f"✅ Updating credits: 0 -> {final_credits}")
                    existing_record.final_credits = final_credits
                else:
                    print(f"⏭️ Credits already awarded ({existing_record.final_credits}), not changing")
                
                await session.commit()
                print(f"✅ Updated existing record")
                return
            
            # No duplicate - create NEW record
            print(f"✅ New commit {commit_hash[:7]}, creating record")
            
            repo = Repository(
                repo_url=repo_url,
                repo_fingerprint=commit_hash,
                owner=owner,
                name=repo_name,
                user_id=user_id,
                final_credits=final_credits,
                sfia_level=sfia_level,
                validation_result=validation if validation else None,
                scan_metrics=state.get("scan_metrics"),
                sfia_result=sfia_result if sfia_result else None,
                audit_result=state.get("audit_result"),
                opik_trace_id=state.get("opik_trace_id"),
                errors=state.get("errors", [])
            )
            
            session.add(repo)
            await session.commit()
            
            print(f"✅ Database: Saved repository record ({repo.id})")
            
            # Create ledger entry
            if final_credits > 0:
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
            # Don't re-raise - allow analysis to complete

async def get_user_total_credits(user_id: str) -> float:
    """Get total credits for a user"""
    async with async_session() as session:
        result = await session.execute(
            select(func.sum(CreditLedger.credits_awarded))
            .where(CreditLedger.user_id == user_id)
        )
        total = result.scalar()
        return total or 0.0