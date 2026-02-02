# backend/app/scripts/setup_online_evals.py
import logging
import opik
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- PROMPTS ---
# Note: We removed the instruction to return a "reason" field since the API 
# currently only supports storing numeric scores for automated rules.

HALLUCINATION_PROMPT = """
You are an expert judge evaluating the faithfulness of an AI-generated answer.
Analyze the provided INPUT and OUTPUT.

Check if the OUTPUT contains information that is not present in the INPUT or contradicts it.
If the OUTPUT references files, metrics, or data that were not provided in the INPUT context, it is a hallucination.

Return a JSON object with a single key "score":
- "score": A float between 0.0 (Hallucinated/Unfaithful) and 1.0 (Faithful/Correct)
"""

RELEVANCE_PROMPT = """
Evaluate the relevance of the AI-generated OUTPUT to the user's INPUT.
Determine if the output directly addresses the user's request or analyzes the provided repository URL correctly.

Return a JSON object with a single key "score":
- "score": A float between 0.0 (Irrelevant) and 1.0 (Highly Relevant)
"""

def configure_platform():
    # 1. Initialize Opik Client
    print(f"⚙️  Initializing Opik Client for workspace: {settings.OPIK_WORKSPACE}")
    try:
        client = opik.Opik(
            project_name=settings.OPIK_PROJECT_NAME,
            api_key=settings.OPIK_API_KEY,
            workspace=settings.OPIK_WORKSPACE,
            host="https://www.comet.com/opik/api"
        )
    except Exception as e:
        print(f"❌ Failed to initialize Opik client: {e}")
        return

    # 2. Get Project ID
    project_id = None
    try:
        projects_response = client.rest_client.projects.find_projects(
            name=settings.OPIK_PROJECT_NAME
        )
        if projects_response.content:
            project_id = projects_response.content[0].id
            print(f"✅ Found Project ID: {project_id}")
        else:
            print(f"✨ Creating new project...")
            client.rest_client.projects.create_project(name=settings.OPIK_PROJECT_NAME)
            projects_response = client.rest_client.projects.find_projects(name=settings.OPIK_PROJECT_NAME)
            project_id = projects_response.content[0].id
            
    except Exception as e:
        print(f"❌ Critical Error: Could not manage Project ID. {e}")
        return

    # 3. Create Feedback Definitions (Workspace Level)
    try:
        # FIX 1: Removed 'project_id' argument. This is now workspace-wide.
        defs = client.rest_client.feedback_definitions.find_feedback_definitions(
            name="user_satisfaction"
        )
        if not defs.content:
            client.rest_client.feedback_definitions.create_feedback_definition(
                request={
                    "name": "user_satisfaction",
                    "type": "numerical",
                    "details": {"min": 0, "max": 1}
                }
            )
            print("✅ Feedback definition 'user_satisfaction' created")
        else:
            print("ℹ️  Feedback definition 'user_satisfaction' already exists")
    except Exception as e:
        print(f"⚠️  Feedback definition sync warning: {e}")

    # 4. Define Online Evaluation Rules
    rules_config = [
        {
            "name": "Grader_Hallucination_Watch",
            "prompt": HALLUCINATION_PROMPT,
            "sampling_rate": 1.0, # Analyze 100% of traces for the demo
            "model": "gpt-4o-mini" # CHANGED: Using the free Opik model
        },
        {
            "name": "Response_Relevance_Check",
            "prompt": RELEVANCE_PROMPT,
            "sampling_rate": 1.0, 
            "model": "gpt-4o-mini" # CHANGED: Using the free Opik model
        }
    ]

    print("\n⚙️  Syncing Online Evaluation Rules...")
    for rule in rules_config:
        try:
            # Check if rule exists
            existing = client.rest_client.automation_rule_evaluators.find_evaluators(
                project_id=project_id,
                name=rule["name"]
            )
            
            # If exists, skip (You must delete in UI to update)
            if existing.content:
                print(f"ℹ️  Rule '{rule['name']}' already exists. Please delete it in UI to update model.")
                continue

            # Construct the Rule Payload
            request_payload = {
                "name": rule["name"],
                "project_id": project_id,
                "type": "llm_as_judge",
                "action": "evaluator",
                "sampling_rate": rule["sampling_rate"],
                "enabled": True,
                "code": {
                    "model": {
                        "name": rule["model"], 
                        "temperature": 0.0
                    },
                    "messages": [
                        {"role": "system", "content": "You are a helpful AI judge. Respond with valid JSON."},
                        {"role": "user", "content": rule["prompt"]}
                    ],
                    "variables": {
                        "input": "input", 
                        "output": "output"
                    },
                    # FIX 2: Removed "reason" field. 
                    # Opik only allows DOUBLE, INTEGER, or BOOLEAN here.
                    "schema": [
                        {
                            "name": "score", 
                            "type": "DOUBLE", 
                            "description": "Computed metric score between 0.0 and 1.0"
                        }
                    ]
                }
            }

            client.rest_client.automation_rule_evaluators.create_automation_rule_evaluator(
                request=request_payload
            )
            print(f"✅ Created Rule: {rule['name']} using {rule['model']}")

        except Exception as e:
            print(f"⚠️  Failed to create rule '{rule['name']}': {e}")

    print("\n✅ Platform Configuration Complete!")

if __name__ == "__main__":
    configure_platform()