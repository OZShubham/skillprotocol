import opik
import inspect

client = opik.Opik()

print(f"SDK Version: {opik.__version__}")

# 1. Check Project Creation Signature
print("\n--- Project Creation Signature ---")
try:
    print(inspect.signature(client.rest_client.projects.create_project))
except Exception as e:
    print(f"Could not get signature: {e}")

# 2. Check Rule Evaluator Signature
print("\n--- Rule Evaluator Creation Signature ---")
try:
    print(inspect.signature(client.rest_client.automation_rule_evaluators.create_automation_rule_evaluator))
except Exception as e:
    print(f"Could not get signature: {e}")

# 3. Check Feedback Definition Signature
print("\n--- Feedback Definition Signature ---")
try:
    print(inspect.signature(client.rest_client.feedback_definitions.create_feedback_definition))
except Exception as e:
    print(f"Could not get signature: {e}")

import opik
import inspect

print("Opik version:", opik.__version__)
print("\nOpik.__init__ signature:")
print(inspect.signature(opik.Opik.__init__))