"""
Prompt Manager - FIXED VERSION
Proper error handling and fallback mechanisms for Opik + Gemini integration.
"""

import logging
from typing import Any, Dict, Optional
import opik
from google import genai
from google.genai import types
from app.core.config import settings

logger = logging.getLogger(__name__)

class PromptLibraryManager:
    """
    Production Manager for Opik Prompt Library and Gemini 3 execution.
    Includes proper error handling and fallback mechanisms.
    """
    
    def __init__(self):
        # High-level Opik client for library access
        try:
            self.opik_client = opik.Opik(
                project_name=settings.OPIK_PROJECT_NAME,
                api_key=settings.OPIK_API_KEY,
                workspace=settings.OPIK_WORKSPACE,
                host="https://www.comet.com/opik/api"
            )
            self.opik_available = True
            logger.info("[PromptManager] Opik client initialized")
        except Exception as e:
            logger.error(f"[PromptManager] Opik init failed: {e}")
            self.opik_client = None
            self.opik_available = False
        
        # Native Google GenAI SDK
        try:
            self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.gemini_available = True
            logger.info("[PromptManager] Gemini client initialized")
        except Exception as e:
            logger.error(f"[PromptManager] Gemini init failed: {e}")
            self.gemini_client = None
            self.gemini_available = False

    def get_library_prompt(self, name: str, commit: Optional[str] = None) -> Any:
        """
        Retrieves a prompt object from the Opik Library.
        
        Args:
            name: Prompt name in Opik (e.g., "judge-agent-rubric")
            commit: Optional specific version
            
        Returns:
            Prompt object
            
        Raises:
            ValueError: If prompt not found or Opik unavailable
        """
        if not self.opik_available:
            raise ValueError("Opik client not available")
        
        try:
            prompt = self.opik_client.get_prompt(name=name, commit=commit)
            
            if not prompt:
                raise ValueError(f"Prompt '{name}' not found in Opik Library")
            
            logger.info(f"[PromptManager] Retrieved prompt '{name}' from Opik")
            return prompt
            
        except Exception as e:
            logger.error(f"[PromptManager] Opik retrieval error [{name}]: {e}")
            raise

    def format_prompt(self, name: str, variables: Dict[str, Any]) -> str:
        """
        Fetches and formats prompt using Mustache syntax.
        
        Args:
            name: Prompt name in Opik
            variables: Dictionary of template variables
            
        Returns:
            Formatted prompt string
            
        Raises:
            ValueError: If prompt fetch or formatting fails
        """
        try:
            prompt_obj = self.get_library_prompt(name)
            formatted = prompt_obj.format(**variables)
            
            logger.debug(
                f"[PromptManager] Formatted prompt '{name}' "
                f"({len(formatted)} chars, {len(variables)} vars)"
            )
            
            return formatted
            
        except Exception as e:
            logger.error(f"[PromptManager] Format error [{name}]: {e}")
            raise ValueError(f"Failed to format prompt '{name}': {str(e)}")

    async def call_gemini(
        self,
        prompt_text: str,
        thinking_level: str = "low",
        temperature: float = 1.0,
        max_retries: int = 2
    ) -> str:
        """
        Executes a Gemini 3 Flash request with Thinking Config.
        
        Args:
            prompt_text: The formatted prompt
            thinking_level: "low", "medium", or "high" (default: "low")
            temperature: Temperature for generation (default: 1.0)
            max_retries: Number of retry attempts (default: 2)
            
        Returns:
            JSON string response from Gemini
            
        Raises:
            ValueError: If Gemini unavailable or request fails
        """
        if not self.gemini_available:
            raise ValueError("Gemini client not available")
        
        # Validate thinking level
        valid_levels = {"low", "medium", "high"}
        if thinking_level not in valid_levels:
            logger.warning(
                f"[PromptManager] Invalid thinking level '{thinking_level}', "
                f"using 'low'"
            )
            thinking_level = "low"
        
        # Build config
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level=thinking_level),
            temperature=temperature,
            response_mime_type="application/json"
        )
        
        # Retry loop
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(
                    f"[PromptManager] Calling Gemini 3 Flash "
                    f"(thinking={thinking_level}, attempt={attempt + 1})"
                )
                
                response = self.gemini_client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=prompt_text,
                    config=config
                )
                
                # Extract text
                response_text = response.text
                
                if not response_text or not response_text.strip():
                    raise ValueError("Gemini returned empty response")
                
                logger.info(
                    f"[PromptManager] Gemini response received "
                    f"({len(response_text)} chars)"
                )
                
                return response_text
                
            except Exception as e:
                last_error = e
                logger.error(
                    f"[PromptManager] Gemini call failed (attempt {attempt + 1}): {e}"
                )
                
                # Don't retry on certain errors
                if "quota" in str(e).lower() or "authentication" in str(e).lower():
                    break
                
                # Wait before retry (exponential backoff)
                if attempt < max_retries:
                    import asyncio
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    logger.info(f"[PromptManager] Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
        
        # All retries failed
        raise ValueError(
            f"Gemini request failed after {max_retries + 1} attempts: {last_error}"
        )

    def is_healthy(self) -> Dict[str, bool]:
        """
        Check health status of both Opik and Gemini connections.
        
        Returns:
            Dictionary with health status
        """
        return {
            "opik_available": self.opik_available,
            "gemini_available": self.gemini_available,
            "fully_operational": self.opik_available and self.gemini_available
        }


# ============================================================================
# GLOBAL SINGLETON
# ============================================================================

_prompt_manager_instance = None

def get_prompt_manager() -> PromptLibraryManager:
    """Get singleton instance of PromptLibraryManager"""
    global _prompt_manager_instance
    
    if _prompt_manager_instance is None:
        _prompt_manager_instance = PromptLibraryManager()
        
        # Log initial health status
        health = _prompt_manager_instance.is_healthy()
        logger.info(f"[PromptManager] Health: {health}")
        
        if not health["fully_operational"]:
            logger.warning(
                "[PromptManager] NOT FULLY OPERATIONAL - "
                "Some agents may fail. Check API keys."
            )
    
    return _prompt_manager_instance


# Create singleton on import
prompt_manager = get_prompt_manager()


# ============================================================================
# HEALTH CHECK ENDPOINT (Optional - for FastAPI)
# ============================================================================

def get_health_status() -> Dict[str, Any]:
    """
    Get detailed health status for monitoring.
    Can be exposed as API endpoint in routes.py
    """
    manager = get_prompt_manager()
    health = manager.is_healthy()
    
    return {
        "status": "healthy" if health["fully_operational"] else "degraded",
        "components": {
            "opik": {
                "available": health["opik_available"],
                "workspace": settings.OPIK_WORKSPACE if health["opik_available"] else None,
                "project": settings.OPIK_PROJECT_NAME if health["opik_available"] else None
            },
            "gemini": {
                "available": health["gemini_available"],
                "model": "gemini-3-flash-preview" if health["gemini_available"] else None
            }
        },
        "issues": [] if health["fully_operational"] else [
            "Opik unavailable" if not health["opik_available"] else None,
            "Gemini unavailable" if not health["gemini_available"] else None
        ]
    }