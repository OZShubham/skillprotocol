# backend/app/api/dashboard_routes.py

from fastapi import APIRouter, HTTPException, Depends
from app.core.opik_config import OpikManager, MAIN_PROJECT
from app.models.database import get_db, Repository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/opik/dashboard-stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    REAL DATA - Query actual analyses from database
    """
    
    try:
        # 1. Get total analyses from database
        result = await db.execute(select(func.count(Repository.id)))
        total_analyses = result.scalar() or 0
        
        # 2. Calculate actual accuracy from database
        # Query repositories with both sfia_result and validation_result
        result = await db.execute(
            select(Repository).where(
                Repository.sfia_result.isnot(None),
                Repository.validation_result.isnot(None)
            ).limit(100)
        )
        repos = result.scalars().all()
        
        if not repos:
            # No data yet - return safe defaults
            return {
                "total_analyses": total_analyses,
                "current_accuracy": 0.0,
                "baseline_accuracy": 0.0,
                "improvement_percentage": 0.0,
                "ab_test_results": None,
                "quality_trend": [],
                "last_updated": datetime.utcnow().isoformat(),
                "opik_dashboard_url": f"https://www.comet.com/{_get_workspace()}/opik/projects/{MAIN_PROJECT}"
            }
        
        # 3. Calculate accuracy (LLM vs Bayesian agreement)
        agreements = []
        for repo in repos:
            sfia_level = repo.sfia_result.get("sfia_level") if repo.sfia_result else None
            bayesian_level = repo.validation_result.get("bayesian_best_estimate") if repo.validation_result else None
            
            if sfia_level and bayesian_level:
                # Agreement if within 1 level
                agreement = abs(sfia_level - bayesian_level) <= 1
                agreements.append(agreement)
        
        current_accuracy = sum(agreements) / len(agreements) if agreements else 0.0
        baseline_accuracy = 0.78  # Initial baseline before optimization
        improvement = ((current_accuracy - baseline_accuracy) / baseline_accuracy) * 100
        
        # 4. A/B Test Results (if you're running experiments)
        ab_results = await _get_real_ab_results(repos)
        
        # 5. Quality trend (last 7 days)
        quality_trend = await _get_quality_trend(db, days=7)
        
        return {
            "total_analyses": total_analyses,
            "current_accuracy": current_accuracy,
            "baseline_accuracy": baseline_accuracy,
            "improvement_percentage": improvement,
            "ab_test_results": ab_results,
            "quality_trend": quality_trend,
            "last_updated": datetime.utcnow().isoformat(),
            "opik_dashboard_url": f"https://www.comet.com/{_get_workspace()}/opik/projects/{MAIN_PROJECT}"
        }
        
    except Exception as e:
        print(f"❌ Dashboard stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_real_ab_results(repos: list) -> Dict[str, Any]:
    """
    Calculate real A/B test results from repository data
    """
    
    # Group by prompt version (if you're tracking this in metadata)
    variant_a_results = []
    variant_b_results = []
    
    for repo in repos:
        # Check if this analysis used Bayesian anchoring
        experiment_config = repo.sfia_result.get("experiment_config", {}) if repo.sfia_result else {}
        bayesian_enabled = experiment_config.get("statistical_hint_enabled", False)
        
        sfia_level = repo.sfia_result.get("sfia_level") if repo.sfia_result else None
        bayesian_level = repo.validation_result.get("bayesian_best_estimate") if repo.validation_result else None
        
        if sfia_level and bayesian_level:
            agreement = abs(sfia_level - bayesian_level) <= 1
            confidence = repo.sfia_result.get("confidence", 0) if repo.sfia_result else 0
            
            result = {
                "agreement": agreement,
                "confidence": confidence
            }
            
            if bayesian_enabled:
                variant_b_results.append(result)
            else:
                variant_a_results.append(result)
    
    # Calculate success rates
    def calc_success_rate(results):
        if not results:
            return 0.0
        return sum(1 for r in results if r["agreement"]) / len(results)
    
    def calc_avg_confidence(results):
        if not results:
            return 0.0
        return sum(r["confidence"] for r in results) / len(results)
    
    a_success = calc_success_rate(variant_a_results)
    b_success = calc_success_rate(variant_b_results)
    
    if not variant_a_results or not variant_b_results:
        return None  # Not enough data for A/B test
    
    return {
        "experiment_name": "bayesian-anchoring-v2",
        "winner": "b" if b_success > a_success else "a",
        "improvement_percentage": ((b_success - a_success) / a_success) * 100 if a_success > 0 else 0,
        "variant_a": {
            "name": "Baseline (No Prior)",
            "success_rate": a_success,
            "sample_size": len(variant_a_results),
            "avg_confidence": calc_avg_confidence(variant_a_results)
        },
        "variant_b": {
            "name": "Bayesian Anchored",
            "success_rate": b_success,
            "sample_size": len(variant_b_results),
            "avg_confidence": calc_avg_confidence(variant_b_results)
        }
    }


async def _get_quality_trend(db: AsyncSession, days: int = 7) -> list:
    """
    Calculate quality trend over time
    """
    
    trend = []
    
    for day_offset in range(days, 0, -1):
        target_date = datetime.utcnow() - timedelta(days=day_offset)
        
        # Query repos created on this day
        result = await db.execute(
            select(Repository).where(
                func.date(Repository.created_at) == target_date.date(),
                Repository.sfia_result.isnot(None),
                Repository.validation_result.isnot(None)
            )
        )
        day_repos = result.scalars().all()
        
        if day_repos:
            agreements = []
            for repo in day_repos:
                sfia_level = repo.sfia_result.get("sfia_level") if repo.sfia_result else None
                bayesian_level = repo.validation_result.get("bayesian_best_estimate") if repo.validation_result else None
                
                if sfia_level and bayesian_level:
                    agreement = abs(sfia_level - bayesian_level) <= 1
                    agreements.append(agreement)
            
            accuracy = sum(agreements) / len(agreements) if agreements else 0.0
            trend.append({
                "index": days - day_offset + 1,
                "accuracy": accuracy
            })
    
    return trend


def _get_workspace() -> str:
    from app.core.config import settings
    return getattr(settings, 'OPIK_WORKSPACE', 'default')