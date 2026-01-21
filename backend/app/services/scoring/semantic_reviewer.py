"""
LLM-Based Semantic Code Reviewer
This actually READS the code like a human would
"""

from openai import AsyncOpenAI
from app.core.config import settings
from typing import Dict, List
import json
from app.core.opik_config import track_agent

class SemanticCodeReviewer:
    """
    Uses LLM to understand CODE MEANING, not just syntax
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.LLM_BASE_URL
        )
    
    async def review_file(self, file_content: str, file_path: str) -> Dict:
        """
        Have LLM read actual code and judge quality
        """
        
        # Truncate if too long (stay within token limits)
        if len(file_content) > 3000:
            file_content = file_content[:3000] + "\n# ... (truncated)"
        
        prompt = f"""You are a Senior Code Reviewer. Analyze this code file:

**File:** {file_path}

```
{file_content}
```

Evaluate on these dimensions:

1. **Algorithm Efficiency** (1-10)
   - Is this optimal or naive?
   - Any obvious performance issues?

2. **Design Quality** (1-10)
   - Is architecture sound?
   - Are responsibilities separated?
   - Is it maintainable?

3. **Error Handling** (1-10)
   - Are edge cases covered?
   - Is error handling robust?

4. **Code Sophistication** (1-10)
   - Does this show advanced knowledge?
   - Is it production-grade?

5. **Domain Complexity** (1-10)
   - How hard was the problem being solved?
   - Does it require specialized knowledge?

Return ONLY valid JSON:
{{
  "algorithm_efficiency": 7,
  "design_quality": 8,
  "error_handling": 6,
  "sophistication": 7,
  "domain_complexity": 8,
  "overall_score": 7.2,
  "key_strengths": ["Uses dependency injection", "Proper async handling"],
  "key_weaknesses": ["Missing input validation", "No unit tests"],
  "estimated_sfia_contribution": 4
}}
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a senior code reviewer who understands code semantics deeply."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            review = json.loads(response.choices[0].message.content)
            return review
            
        except Exception as e:
            print(f"⚠️ LLM review failed for {file_path}: {e}")
            return {
                "overall_score": 5.0,
                "error": str(e)
            }
    @track_agent(name="Semantic Review", agent_type="llm")
    async def review_repository_sample(
        self, 
        repo_path: str, 
        sample_files: List[str]
    ) -> Dict:
        """
        Review a sample of important files
        """
        
        reviews = []
        
        for file_path in sample_files[:5]:  # Limit to 5 files (cost control)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                review = await self.review_file(content, file_path)
                reviews.append(review)
                
            except Exception as e:
                print(f"⚠️ Could not review {file_path}: {e}")
                continue
        
        if not reviews:
            return {"semantic_multiplier": 1.0}
        
        # Aggregate scores
        avg_overall = sum(r.get('overall_score', 5.0) for r in reviews) / len(reviews)
        
        # Calculate multiplier (5.0 = neutral, <5 = penalty, >5 = bonus)
        semantic_multiplier = 0.5 + (avg_overall / 10.0)
        
        # Extract key insights
        all_strengths = []
        all_weaknesses = []
        for review in reviews:
            all_strengths.extend(review.get('key_strengths', []))
            all_weaknesses.extend(review.get('key_weaknesses', []))
        
        return {
            'semantic_multiplier': round(semantic_multiplier, 2),
            'average_score': round(avg_overall, 2),
            'reviews_count': len(reviews),
            'key_strengths': list(set(all_strengths))[:5],
            'key_weaknesses': list(set(all_weaknesses))[:5],
        }


