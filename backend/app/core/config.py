# from pydantic_settings import BaseSettings
# from pydantic import Field

# class Settings(BaseSettings):
    
#     # 1. Load the raw string from .env
#     DATABASE_URL_RAW: str = Field(..., alias="DATABASE_URL")

#     @property
#     def DATABASE_URL(self) -> str:
#         """
#         Sanitizes the Neon URL specifically for asyncpg.
#         """
#         url = self.DATABASE_URL_RAW
        
#         # 1. Parse the URL to remove all query params (sslmode, channel_binding, etc.)
#         # This fixes the "unexpected keyword argument" errors
#         if "?" in url:
#             url = url.split("?")[0]
            
#         # 2. Fix the Protocol (postgres -> postgresql+asyncpg)
#         if url.startswith("postgres://") or url.startswith("postgresql://"):
#             parts = url.split("://", 1)
#             url = f"postgresql+asyncpg://{parts[1]}"
            
#         # 3. Re-add ONLY the SSL parameter that asyncpg supports
#         return f"{url}?ssl=require"
#     # ========================================================================
#     # External APIs & App Config (Keep the rest of your settings)
#     # ========================================================================
#     GITHUB_TOKEN: str = ""
#     # OPENAI_API_KEY: str = ""
#     GROQ_API_KEY: str  # Add this
    
#     # Model configuration
#     LLM_MODEL: str = "llama-3.3-70b-versatile"  # Groq model
#     LLM_BASE_URL: str = "https://api.groq.com/openai/v1"
#     LLM_TEMPERATURE: float = 0.1
#     GEMINI_API_KEY: str
#     OPIK_API_KEY: str = ""
#     OPIK_WORKSPACE: str = "" 
#     OPIK_PROJECT_NAME: str = "skillprotocol"
#     ENVIRONMENT: str = "development"
#     DEBUG: bool = True
#     MAX_REPO_SIZE_KB: int = 500000  
#     CLONE_TIMEOUT_SECONDS: int = 120  # 2 minutes
    
#     CORS_ORIGINS_STR: str = "http://localhost:5173,http://localhost:3000"
#     OPENROUTER_API_KEY: str
#     OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"


#     DEFAULT_LLM_MODEL: str = "google/gemini-2.0-flash-001" 
#     JUDGE_LLM_MODEL: str = "google/gemini-2.0-pro-exp-02-05" # or openai/gpt-4o
#     # Enhanced agent settings
#     GRADER_MAX_ITERATIONS: int = 8  # Max tool-use loops
#     GRADER_CONFIDENCE_THRESHOLD: float = 0.60  # Retry if below
#     REVIEWER_USE_GEMINI: bool = True  # Use Gemini for semantic analysis
#     MENTOR_MAX_ITERATIONS: int = 10  # Max tool-use loops
    
#     # Tool settings
#     ENABLE_CODE_ANALYSIS_TOOLS: bool = True
#     ENABLE_LEARNING_RESOURCE_TOOLS: bool = True
#     TOOL_TIMEOUT_SECONDS: int = 30
    
#     @property
#     def CORS_ORIGINS(self) -> list[str]:
#         return [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",")]

#     class Config:
#         env_file = ".env"
#         extra = "ignore"

# settings = Settings()


"""
Updated Configuration - Using OpenRouter
Single API key for all LLM providers
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    
    # ========================================================================
    # Database Configuration
    # ========================================================================
    DATABASE_URL_RAW: str = Field(..., alias="DATABASE_URL")

    @property
    def DATABASE_URL(self) -> str:
        """Sanitizes the Neon URL for asyncpg"""
        url = self.DATABASE_URL_RAW
        
        if "?" in url:
            url = url.split("?")[0]
            
        if url.startswith("postgres://") or url.startswith("postgresql://"):
            parts = url.split("://", 1)
            url = f"postgresql+asyncpg://{parts[1]}"
            
        return f"{url}?ssl=require"
    
    # ========================================================================
    # OPENROUTER CONFIGURATION (NEW - Replaces GROQ + GEMINI)
    # ========================================================================
    OPENROUTER_API_KEY: str = ""
    
    # OpenRouter endpoint (compatible with OpenAI SDK)
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # Model names (OpenRouter format)
    DEFAULT_MODEL: str = "google/gemini-3-flash-preview"
    GRADER_MODEL: str = "google/gemini-3-flash-preview"
    JUDGE_MODEL: str = "google/gemini-3-flash-preview"
    MENTOR_MODEL: str = "google/gemini-3-flash-preview"
    SEMANTIC_MODEL: str = "google/gemini-3-flash-preview"
    
    # LLM Settings
    TEMPERATURE: float = 0.1
    MAX_TOKENS: int = 4000
    
    # Alternative models you can use:
    # - "openai/gpt-4-turbo" - GPT-4 (more expensive)
    # - "anthropic/claude-sonnet-4" - Claude (very good reasoning)
    # - "meta-llama/llama-3.3-70b-instruct" - Llama (open source)
    # - "deepseek/deepseek-chat" - DeepSeek (very cheap)
    
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_RETRIES: int = 3
    
    # ========================================================================
    # GitHub Configuration
    # ========================================================================
    GITHUB_TOKEN: str = ""
    
    
    
    # ========================================================================
    # Opik Configuration (Unchanged)
    # ========================================================================
    OPIK_API_KEY: str = ""
    OPIK_WORKSPACE: str = ""
    OPIK_PROJECT_NAME: str = "skillprotocol"
    
    # ========================================================================
    # Application Settings
    # ========================================================================
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    MAX_REPO_SIZE_KB: int = 500000
    CLONE_TIMEOUT_SECONDS: int = 120
    
    CORS_ORIGINS_STR: str = "https://skillprotocol.vercel.app , https://skillprotocol-9l4upf7ei-ozshubhams-projects.vercel.app, https://skillprotocol-git-master-ozshubhams-projects.vercel.app, http://localhost:5173,http://localhost:3000"
    
    @property
    def CORS_ORIGINS(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",")]
    
    # ========================================================================
    # Agent Configuration
    # ========================================================================
    GRADER_MAX_ITERATIONS: int = 8
    GRADER_CONFIDENCE_THRESHOLD: float = 0.60
    MENTOR_MAX_ITERATIONS: int = 10
    
    ENABLE_CODE_ANALYSIS_TOOLS: bool = True
    ENABLE_LEARNING_RESOURCE_TOOLS: bool = True
    TOOL_TIMEOUT_SECONDS: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"



settings = Settings()
    
