# test_opik_prompts.py
import opik
from app.core.config import settings

client = opik.Opik(
    project_name=settings.OPIK_PROJECT_NAME,
    api_key=settings.OPIK_API_KEY,
    workspace=settings.OPIK_WORKSPACE,
    host="https://www.comet.com/opik/api"
)

required_prompts = [
    "reviewer-agent-deposition",
    "judge-agent-rubric",
    "sfia-grader-v2"  # Optional - will fallback to engine.py
]

print("🔍 Checking Opik Prompt Library...\n")

for prompt_name in required_prompts:
    try:
        prompt = client.get_prompt(name=prompt_name)
        print(f"✅ Found: {prompt_name}")
    except Exception as e:
        print(f"❌ Missing: {prompt_name} - {str(e)}")