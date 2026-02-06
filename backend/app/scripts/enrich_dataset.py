"""
Dataset Enrichment Script (FIXED)
Backfills missing context by re-analyzing existing dataset items.
Fixes: Handles Opik SDK returning dicts instead of objects.
"""

import asyncio
import uuid
import logging
import os
import json
import opik
from app.core.config import settings
from app.agents.graph import run_analysis

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CONFIGURATION
SOURCE_DATASET = "sfia-golden-v1" 
TARGET_DATASET = "sfia-golden-enriched" 

async def enrich_data():
    print(f"\n🚀 Starting Enrichment: {SOURCE_DATASET} -> {TARGET_DATASET}")
    
    # 1. Initialize Opik
    if settings.OPIK_API_KEY:
        os.environ["OPIK_API_KEY"] = settings.OPIK_API_KEY
        
    client = opik.Opik(project_name=settings.OPIK_PROJECT_NAME)
    
    # 2. Get Datasets
    try:
        # SDK 3.0+ Fix: Ensure we get the dataset object correctly
        source_ds = client.get_dataset(name=SOURCE_DATASET)
        if not source_ds:
            print(f"❌ Source dataset '{SOURCE_DATASET}' not found!")
            return

        target_ds = client.get_or_create_dataset(name=TARGET_DATASET)
        
        # This returns a list of DICTIONARIES, not objects
        items = source_ds.get_items()
        print(f"📦 Found {len(items)} items to enrich.")
    except Exception as e:
        print(f"❌ Dataset error: {e}")
        return

    success_count = 0

    # 3. Iterate and Re-Analyze
    for item in items:
        # --- FIX 1: Use Dictionary Access (['key']) instead of Dot Notation (.key) ---
        input_data = item.get("input")
        expected_level = item.get("expected_sfia_level")
        expected_output = item.get("expected_output")
        
        # Handle various input formats
        repo_url = None
        
        if isinstance(input_data, str):
            if "github.com" in input_data and not input_data.strip().startswith("{"):
                repo_url = input_data.strip()
            else:
                # Try parsing if it's a JSON string
                try:
                    data = json.loads(input_data)
                    # Check for nested state or direct key
                    if isinstance(data, dict):
                        repo_url = data.get("state", {}).get("repo_url") or data.get("repo_url")
                except: pass
                
        elif isinstance(input_data, dict):
            repo_url = input_data.get("repo_url") or input_data.get("input")
            # Handle nested state dict
            if not repo_url and "state" in input_data:
                repo_url = input_data["state"].get("repo_url")

        if not repo_url:
            print(f"⏩ Skipping invalid item input: {str(input_data)[:30]}...")
            continue

        print(f"\n🔄 Re-analyzing: {repo_url}")
        
        try:
            # --- RUN THE AGENT PIPELINE ---
            job_id = f"enrich_{uuid.uuid4().hex[:8]}"
            
            # This runs your actual backend code
            final_state = await run_analysis(
                repo_url=repo_url,
                user_id="enrichment_bot",
                job_id=job_id
            )
            
            # --- EXTRACT RICH CONTEXT ---
            # Safe .get() chains to avoid crashes if analysis fails partially
            ncrf = final_state.get("scan_metrics", {}).get("ncrf", {})
            sfia = final_state.get("sfia_result", {})
            val = final_state.get("validation_result", {})
            
            # --- MERGE WITH ORIGINAL TRUTH ---
            # We trust your old dataset's "expected_sfia_level"
            truth_level = expected_level if expected_level is not None else expected_output
            
            rich_item = {
                "input": repo_url,
                "expected_sfia_level": int(truth_level) if truth_level else 0,
                "expected_output": str(truth_level) if truth_level else "0",
                
                # The "Thick" Data needed for Optimization
                "sloc": ncrf.get("total_sloc", 0),
                "learning_hours": ncrf.get("estimated_learning_hours", 0),
                "credits": ncrf.get("ncrf_base_credits", 0),
                
                "grader_level": int(sfia.get("sfia_level", 0)),
                "grader_reasoning": sfia.get("reasoning", "No reasoning generated"),
                
                "bayesian_level": int(val.get("bayesian_best_estimate", 0)),
                "bayesian_confidence": float(val.get("confidence", 0.0)),
                
                "metadata": {
                    "original_source": SOURCE_DATASET,
                    "enrichment_run": True,
                    "job_id": job_id
                }
            }
            
            # Insert uses a list of items
            target_ds.insert([rich_item])
            success_count += 1
            print(f"✅ Enriched & Saved (Truth: L{rich_item['expected_sfia_level']})")

        except Exception as e:
            print(f"❌ Failed to analyze {repo_url}: {e}")
            continue

    print(f"\n🎉 Enrichment Complete!")
    print(f"   📂 New Dataset: '{TARGET_DATASET}'")
    print(f"   📊 Rows: {success_count}")

if __name__ == "__main__":
    asyncio.run(enrich_data())