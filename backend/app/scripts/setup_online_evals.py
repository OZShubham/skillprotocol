# backend/app/scripts/setup_online_evals.py
"""
Setup Script - STRICTLY COMPLIANT WITH OPIK 1.9.96 REST API
"""
import logging
import opik
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HALLUCINATION_PROMPT = """
You are an expert judge evaluating the faithfulness of an AI-generated answer.
Analyze the INPUT, CONTEXT, and OUTPUT.
Return JSON with "score" (0.0 to 1.0) and "reason".
"""

RELEVANCE_PROMPT = """
Evaluate the relevance of an AI-generated answer to the user's input.
Return JSON with "score" (0.0 to 1.0) and "reason".
"""

def configure_platform():
    # ✅ CORRECT for Opik 0.1.96: Use 'host' parameter
    client = opik.Opik(
        project_name=settings.OPIK_PROJECT_NAME,
        api_key=settings.OPIK_API_KEY,
        workspace=settings.OPIK_WORKSPACE,
        host="https://www.comet.com/opik/api"  # ← CORRECT parameter name
    )
    
    print(f"⚙️  Configuring Opik Project: {settings.OPIK_PROJECT_NAME}")

    try:
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
            print("ℹ️  Feedback definition 'user_satisfaction' exists")
    except Exception as e:
        print(f"⚠️  Feedback definition sync failed: {e}")

    project_id = None
    try:
        projects_response = client.rest_client.projects.find_projects(
            name=settings.OPIK_PROJECT_NAME
        )
        
        if projects_response.content:
            project_id = projects_response.content[0].id
            print(f"✅ Found Project ID: {project_id}")
        else:
            client.rest_client.projects.create_project(
                name=settings.OPIK_PROJECT_NAME,
                description="SkillProtocol Skill Verification and Monitoring"
            )
            projects_response = client.rest_client.projects.find_projects(
                name=settings.OPIK_PROJECT_NAME
            )
            project_id = projects_response.content[0].id
            print(f"✅ Created Project ID: {project_id}")
            
    except Exception as e:
        print(f"❌ Critical Error: Could not manage Project ID. {e}")
        return

    rules_config = [
        {"name": "grader_hallucination_check", "prompt": HALLUCINATION_PROMPT, "sampling_rate": 0.1},
        {"name": "certificate_relevance_check", "prompt": RELEVANCE_PROMPT, "sampling_rate": 0.1}
    ]

    for rule in rules_config:
        try:
            existing = client.rest_client.automation_rule_evaluators.find_evaluators(
                project_id=project_id,
                name=rule["name"]
            )
            
            if existing.content:
                print(f"ℹ️  Rule '{rule['name']}' already exists")
                continue

            request_payload = {
                "name": rule["name"],
                "project_id": project_id,
                "type": "llm_as_judge",
                "action": "evaluator",
                "sampling_rate": rule["sampling_rate"],
                "enabled": True,
                "code": {
                    # CHANGE: Point to Groq and your preferred model
                    "model": {
                        "name": "groq/llama-3.3-70b-versatile", 
                        "temperature": 0.0
                    },
                    "messages": [
                        {"role": "system", "content": "You are a helpful AI judge. Respond with valid JSON."},
                        {"role": "user", "content": rule["prompt"]}
                    ],
                    "variables": {"input": "input", "output": "output"},
                    "schema": [
                        {"name": "score", "type": "DOUBLE", "description": "Computed metric score between 0.0 and 1.0"}
                    ]
                }
            }

            client.rest_client.automation_rule_evaluators.create_automation_rule_evaluator(
                request=request_payload
            )
            print(f"✅ Online Rule '{rule['name']}' synced to Opik using Groq")

        except Exception as e:
            print(f"⚠️  Rule creation failed for '{rule['name']}': {e}")


if __name__ == "__main__":
    configure_platform()