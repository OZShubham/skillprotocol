"""
The Feedback Flywheel Script
Automates the "Data Engine":
1. Fetches traces with User Feedback = 1.0 (Thumbs Up)
2. Adds them to the 'Golden Dataset' for future regression testing
3. Demonstrates the full lifecycle of an AI product for the Hackathon
"""

import opik
from app.core.config import settings

def run_flywheel():
    print(f"\n🔄 Starting Feedback Flywheel for project: {settings.OPIK_PROJECT_NAME}")
    
    # 1. Initialize Client
    client = opik.Opik(
        api_key=settings.OPIK_API_KEY,
        workspace=settings.OPIK_WORKSPACE,
        project_name=settings.OPIK_PROJECT_NAME
    )
    
    # 2. Define/Create the Golden Dataset
    dataset_name = "SkillProtocol-Golden-V1"
    dataset = client.get_or_create_dataset(name=dataset_name)
    print(f"📂 Target Dataset: {dataset_name}")

    # 3. Find High-Quality Traces (The "Gold")
    # We search for traces where the user explicitly gave a thumbs up in the UI
    print("🔍 Searching for positive user feedback...")
    
    try:
        # Note: Opik Query Language syntax
        # We look for feedback scores named 'user_satisfaction' with value 1
        traces = client.search_traces(
            project_name=settings.OPIK_PROJECT_NAME,
            filter_string='feedback_scores.user_satisfaction = 1',
            max_results=100
        )
    except Exception as e:
        print(f"⚠️ Search failed (filter might be invalid): {e}")
        # Fallback: Get recent traces and filter manually in python
        traces = client.search_traces(project_name=settings.OPIK_PROJECT_NAME, max_results=100)

    count = 0
    for trace in traces:
        # Verify feedback (double check logic)
        feedback = trace.feedback_scores or []
        is_good = any(f.name == "user_satisfaction" and f.value == 1.0 for f in feedback)
        
        if is_good:
            # 4. Extract Input/Output pairs
            # We want to train on "Given this Repo URL -> Expect this SFIA Level"
            
            # Input is usually in the trace input
            repo_url = None
            if trace.input:
                repo_url = trace.input.get("repo_url")
            
            # The Output SFIA Level is stored in metadata by the Reporter Agent
            final_level = None
            if trace.metadata:
                final_level = trace.metadata.get("sfia_level")
            
            if repo_url and final_level:
                # 5. Add to Dataset
                # Opik handles deduplication automatically based on content
                dataset.insert([{
                    "input": repo_url,
                    "expected_output": str(final_level),
                    "metadata": {
                        "source_trace_id": trace.id,
                        "mined_at": "flywheel_v1",
                        "judge_ruling": trace.metadata.get("judge_ruling", "")
                    }
                }])
                count += 1
                print(f"   ✨ Mined Trace {trace.id[:8]} -> Added to Dataset (Level {final_level})")

    if count == 0:
        print("ℹ️ No new positive feedback found. Go click 'Thumbs Up' in the UI!")
    else:
        print(f"✅ Flywheel Complete. Added {count} new high-quality examples.")
        print(f"   Run 'python run_evaluation.py' to retrain against this new data!")

if __name__ == "__main__":
    run_flywheel()

# python -m app.scripts.run_feedback_loop