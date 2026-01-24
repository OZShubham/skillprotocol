import json
import logging
from typing import List, Dict, Any
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.prompt_manager import prompt_manager

logger = logging.getLogger(__name__)

class SemanticCodeReviewer:
    """
    Advanced LLM Judge for architectural sophistication and design patterns.
    """

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.LLM_BASE_URL
        )

    async def review_repository_sample(self, sample_files: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Reviews a batch of critical files and generates an 'Expert Testimony' report.
        """
        # Prepare content for LLM
        file_context = ""
        for f in sample_files[:5]: # Review top 3 critical files
            file_context += f"\nFILE: {f['path']}\n```\n{f['content'][:5000]}\n```\n"

        # Task 1.2: Fetch Robust Prompt from Opik Library
        # Prompt name in Opik: 'semantic-reviewer-rubric'
        try:
            formatted_prompt = prompt_manager.format_prompt(
                "semantic-reviewer-rubric",
                {"file_context": file_context}
            )

            response = await self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a Principal Software Architect conducting a forensic audit."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            report = json.loads(response.choices[0].message.content)
            
            # Normalize multiplier (ensure it's between 0.5 and 1.5)
            raw_mult = report.get("semantic_multiplier", 1.0)
            report["semantic_multiplier"] = max(0.5, min(1.5, raw_mult))
            
            return report

        except Exception as e:
            logger.error(f"Semantic Review Failed: {e}")
            return {
                "semantic_multiplier": 1.0,
                "key_insight": "Review failed due to technical error.",
                "sophistication_score": 5,
                "key_strengths": [],
                "key_weaknesses": ["Internal Auditor Error"]
            }