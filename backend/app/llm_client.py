"""
Unified LLM Client Manager
Uses OpenRouter as a single gateway for all LLM providers
Supports: Gemini, GPT-4, Claude, Llama, and more through OpenRouter
"""

import os
import logging
from typing import Optional, Dict, Any, List
from openai import OpenAI, AsyncOpenAI
from enum import Enum
from opik.integrations.openai import track_openai
from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """Supported model providers through OpenRouter"""
    GEMINI_FLASH = "google/gemini-3-flash-preview"
    GEMINI_PRO = "google/gemini-3-pro-preview"
    GPT4 = "openai/gpt-4-turbo"
    CLAUDE_SONNET = "anthropic/claude-sonnet-4"
    LLAMA_70B = "meta-llama/llama-3.3-70b-instruct"
    DEEPSEEK = "deepseek/deepseek-chat"


class ThinkingLevel(Enum):
    """Reasoning effort levels (OpenRouter compatible)"""
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    NONE = "none"


class UnifiedLLMClient:
    def __init__(
        self,
        api_key: str,
        default_model: str = ModelProvider.GEMINI_FLASH.value,
        max_retries: int = 3
    ):
        self.api_key = api_key
        self.default_model = default_model
        self.max_retries = max_retries
        
        # --- OPIK INTEGRATION START ---
        # We explicitly set the project name so these calls go to the right place
        
        # Initialize OpenAI-compatible client & WRAP IT
        raw_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            max_retries=max_retries
        )
        self.client = track_openai(raw_client, project_name=settings.OPIK_PROJECT_NAME)
        
        # Async client & WRAP IT
        raw_async_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            max_retries=max_retries
        )
        self.async_client = track_openai(raw_async_client, project_name=settings.OPIK_PROJECT_NAME)
        # --- OPIK INTEGRATION END ---
        
        logger.info(f"✅ Unified LLM Client initialized with Opik Tracing")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        thinking_level: Optional[ThinkingLevel] = None,
        json_mode: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Standard chat completion with OpenRouter
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to self.default_model)
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            thinking_level: Reasoning effort level (for compatible models)
            json_mode: Force JSON output
            **kwargs: Additional OpenRouter parameters
        
        Returns:
            Response dict with content and metadata
        """
        model = model or self.default_model
        
        # Build request payload
        request_params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            request_params["max_tokens"] = max_tokens
        
        # Enable reasoning for supported models
        if thinking_level and "gemini" in model.lower():
            request_params["extra_body"] = {
                "reasoning": {"enabled": True}
            }
            if thinking_level != ThinkingLevel.NONE:
                request_params["reasoning_effort"] = thinking_level.value
        
        # Force JSON output if needed
        if json_mode:
            request_params["response_format"] = {"type": "json_object"}
        
        # Add any extra parameters
        request_params.update(kwargs)
        
        try:
            response = self.client.chat.completions.create(**request_params)
            
            # Extract reasoning if present
            reasoning_details = None
            if hasattr(response.choices[0].message, 'reasoning_details'):
                reasoning_details = response.choices[0].message.reasoning_details
            
            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "reasoning_details": reasoning_details,
                "finish_reason": response.choices[0].finish_reason
            }
            
        except Exception as e:
            logger.error(f"❌ LLM request failed: {e}")
            raise
    
    async def async_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Async version of chat_completion"""
        model = model or self.default_model
        
        request_params = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        
        try:
            response = await self.async_client.chat.completions.create(**request_params)
            
            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Async LLM request failed: {e}")
            raise
    
    def chat_with_fallback(
        self,
        messages: List[Dict[str, str]],
        fallback_models: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Try multiple models in sequence until one succeeds
        
        Example:
            fallback_models = [
                ModelProvider.GEMINI_FLASH.value,
                ModelProvider.LLAMA_70B.value,
                ModelProvider.GPT4.value
            ]
        """
        if not fallback_models:
            fallback_models = [self.default_model]
        
        last_error = None
        
        for model in fallback_models:
            try:
                logger.info(f"🔄 Trying model: {model}")
                response = self.chat_completion(messages, model=model, **kwargs)
                logger.info(f"✅ Success with {model}")
                return response
                
            except Exception as e:
                logger.warning(f"⚠️  {model} failed: {e}")
                last_error = e
                continue
        
        # All models failed
        raise Exception(f"All fallback models failed. Last error: {last_error}")
    
    def structured_output(
        self,
        messages: List[Dict[str, str]],
        schema: Dict[str, Any],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get structured JSON output conforming to a schema
        
        Args:
            messages: Conversation messages
            schema: JSON schema for the output
            model: Model to use
            **kwargs: Additional parameters
        
        Returns:
            Parsed JSON object
        """
        model = model or self.default_model
        
        # Add schema to system message
        schema_prompt = f"""
You must respond with valid JSON matching this exact schema:

{schema}

Output ONLY the JSON, no markdown, no explanations.
"""
        
        # Prepend schema instructions
        enhanced_messages = [
            {"role": "system", "content": schema_prompt}
        ] + messages
        
        response = self.chat_completion(
            enhanced_messages,
            model=model,
            json_mode=True,
            **kwargs
        )
        
        # Parse and validate JSON
        import json
        try:
            content = response["content"]
            # Strip markdown if present
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            parsed = json.loads(content)
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            raise ValueError(f"Model returned invalid JSON: {content}")


# ============================================================================
# SINGLETON PATTERN
# ============================================================================

_client_instance = None


def get_llm_client(
    api_key: Optional[str] = None,
    default_model: Optional[str] = None
) -> UnifiedLLMClient:
    """
    Get singleton LLM client instance
    
    Usage:
        from app.llm_client import get_llm_client
        
        client = get_llm_client()
        response = client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}]
        )
    """
    global _client_instance
    
    if _client_instance is None:
        if not api_key:
            api_key = os.getenv("OPENROUTER_API_KEY")
            
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not set. "
                "Get your key from https://openrouter.ai/keys"
            )
        
        if not default_model:
            default_model = os.getenv(
                "DEFAULT_LLM_MODEL",
                ModelProvider.GEMINI_FLASH.value
            )
        
        _client_instance = UnifiedLLMClient(
            api_key=api_key,
            default_model=default_model
        )
    
    return _client_instance


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_messages(
    system_prompt: str,
    user_message: str,
    conversation_history: Optional[List[Dict]] = None
) -> List[Dict[str, str]]:
    """Helper to format messages for OpenRouter"""
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    if conversation_history:
        messages.extend(conversation_history)
    
    messages.append({"role": "user", "content": user_message})
    
    return messages