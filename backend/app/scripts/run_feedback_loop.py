"""
The Feedback Flywheel Script
Automates the "Data Engine":
1. Fetches production traces with User Satisfaction = 1.0 (Thumbs Up)
2. Validates they have the necessary data (Input Repo + Output Level)
3. Adds them to the 'sfia-golden-v1' dataset for future regression testing
"""

import json
import logging
import opik
from app.core.config import settings

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
TARGET_DATASET = "sfia-golden-v1"
FEEDBACK_METRIC_NAME = "user_satisfaction"

def run_flywheel():
    print(f"\n🔄 Starting Feedback Flywheel for project: {settings.OPIK_PROJECT_NAME}")
    
    # 1. Initialize Opik Client
    client = opik.Opik(
        api_key=settings.OPIK_API_KEY,
        workspace=settings.OPIK_WORKSPACE,
        project_name=settings.OPIK_PROJECT_NAME
    )
    
    # 2. Get or Create the Golden Dataset
    try:
        dataset = client.get_or_create_dataset(name=TARGET_DATASET)
        print(f"📂 Target Dataset: {TARGET_DATASET}")
    except Exception as e:
        logger.error(f"❌ Failed to get dataset: {e}")
        return

    # 3. Search for High-Quality Traces
    # We use OQL (Opik Query Language) to find traces with specific feedback
    print("🔍 Searching for positive user feedback...")
    
    try:
        # Filter: Feedback is 'user_satisfaction' AND value is 1
        traces = client.search_traces(
            project_name=settings.OPIK_PROJECT_NAME,
            filter_string=f'feedback_scores.{FEEDBACK_METRIC_NAME} = 1',
            max_results=50  # Process batches of 50 to avoid timeouts
        )
    except Exception as e:
        logger.error(f"⚠️ Search failed: {e}")
        return

    print(f"📊 Found {len(traces)} candidate traces.")

    new_items_count = 0
    
    for trace in traces:
        try:
            # 4. Extract Data from Trace
            # Note: Opik SDK might return input/output as dicts or JSON strings depending on how they were logged.
            
            # --- Extract Input (Repo URL) ---
            trace_input = trace.input
            repo_url = None
            
            if isinstance(trace_input, dict):
                repo_url = trace_input.get("repo_url") or trace_input.get("input")
            elif isinstance(trace_input, str):
                # Try parsing stringified JSON
                try:
                    data = json.loads(trace_input)
                    repo_url = data.get("repo_url")
                except:
                    repo_url = trace_input if "github.com" in trace_input else None

            # --- Extract Output (SFIA Level) ---
            # The Reporter Agent logs final_level in metadata, which is the most reliable source
            trace_metadata = trace.metadata or {}
            final_level = trace_metadata.get("sfia_level") or trace_metadata.get("judge_verdict_level")

            # Validation: We need both an input URL and a confirmed Level to learn from this
            if repo_url and final_level:
                
                # 5. Add to Dataset
                # Opik handles deduplication automatically based on content hash
                dataset.insert([{
                    "input": repo_url,
                    "expected_output": str(final_level), # Store as string for consistency
                    "expected_sfia_level": int(final_level),
                    "metadata": {
                        "source_trace_id": trace.id,
                        "mined_at": "feedback_loop_v1",
                        "judge_ruling": trace_metadata.get("judge_ruling", "Human Verified")
                    }
                }])
                
                new_items_count += 1
                print(f"   ✨ Mined Trace {trace.id[:8]} -> Repo: {repo_url} (Level {final_level})")
            
            else:
                logger.debug(f"   Skipping Trace {trace.id[:8]}: Missing data (URL: {repo_url}, Level: {final_level})")

        except Exception as e:
            logger.warning(f"   ⚠️ Error processing trace {trace.id}: {e}")
            continue

    print(f"\n✅ Flywheel Complete.")
    print(f"   📥 Processed: {len(traces)}")
    print(f"   💾 Added: {new_items_count} new validated examples to '{TARGET_DATASET}'")

if __name__ == "__main__":
    run_flywheel()
# python -m app.scripts.run_feedback_loop