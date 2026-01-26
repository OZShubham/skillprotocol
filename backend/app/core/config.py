from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    
    # 1. Load the raw string from .env
    DATABASE_URL_RAW: str = Field(..., alias="DATABASE_URL")

    @property
    def DATABASE_URL(self) -> str:
        """
        Sanitizes the Neon URL specifically for asyncpg.
        """
        url = self.DATABASE_URL_RAW
        
        # 1. Parse the URL to remove all query params (sslmode, channel_binding, etc.)
        # This fixes the "unexpected keyword argument" errors
        if "?" in url:
            url = url.split("?")[0]
            
        # 2. Fix the Protocol (postgres -> postgresql+asyncpg)
        if url.startswith("postgres://") or url.startswith("postgresql://"):
            parts = url.split("://", 1)
            url = f"postgresql+asyncpg://{parts[1]}"
            
        # 3. Re-add ONLY the SSL parameter that asyncpg supports
        return f"{url}?ssl=require"
    # ========================================================================
    # External APIs & App Config (Keep the rest of your settings)
    # ========================================================================
    GITHUB_TOKEN: str = ""
    # OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str  # Add this
    
    # Model configuration
    LLM_MODEL: str = "llama-3.3-70b-versatile"  # Groq model
    LLM_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_TEMPERATURE: float = 0.1
    GEMINI_API_KEY: str
    OPIK_API_KEY: str = ""
    OPIK_WORKSPACE: str = "" 
    OPIK_PROJECT_NAME: str = "skillprotocol"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    MAX_REPO_SIZE_KB: int = 500000  
    CLONE_TIMEOUT_SECONDS: int = 120  # 2 minutes
    
    CORS_ORIGINS_STR: str = "http://localhost:5173,http://localhost:3000"
    
    @property
    def CORS_ORIGINS(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()









# """
# Fixed config.py - Validates GitHub token on startup
# """

# from pydantic_settings import BaseSettings
# from pydantic import Field, validator
# import os

# class Settings(BaseSettings):
    
#     # Database
#     DATABASE_URL_RAW: str = Field(..., alias="DATABASE_URL")

#     @property
#     def DATABASE_URL(self) -> str:
#         """Sanitizes the Neon URL for asyncpg"""
#         url = self.DATABASE_URL_RAW
        
#         if "?" in url:
#             url = url.split("?")[0]
            
#         if url.startswith("postgres://") or url.startswith("postgresql://"):
#             parts = url.split("://", 1)
#             url = f"postgresql+asyncpg://{parts[1]}"
            
#         return f"{url}?ssl=require"
    
#     # ========================================================================
#     # GitHub Configuration
#     # ========================================================================
#     GITHUB_TOKEN: str = ""
    
#     @validator('GITHUB_TOKEN')
#     def validate_github_token(cls, v):
#         """Ensure GitHub token is set"""
#         if not v or v == "":
#             raise ValueError(
#                 "❌ GITHUB_TOKEN is not set in .env file!\n"
#                 "Please add: GITHUB_TOKEN=ghp_your_token_here\n"
#                 "Get token from: https://github.com/settings/tokens"
#             )
        
#         # Basic format check (GitHub tokens start with ghp_, gho_, or ghs_)
#         if not (v.startswith('ghp_') or v.startswith('gho_') or v.startswith('ghs_')):
#             print(f"⚠️  WARNING: GITHUB_TOKEN doesn't look like a valid GitHub token")
#             print(f"   Expected format: ghp_xxxxxxxxxxxx")
#             print(f"   Current value: {v[:10]}...")
        
#         return v
    
#     # ========================================================================
#     # LLM Configuration
#     # ========================================================================
#     GROQ_API_KEY: str = ""
    
#     @validator('GROQ_API_KEY')
#     def validate_groq_key(cls, v):
#         """Ensure Groq API key is set"""
#         if not v or v == "":
#             raise ValueError(
#                 "❌ GROQ_API_KEY is not set in .env file!\n"
#                 "Please add: GROQ_API_KEY=your_groq_key_here\n"
#                 "Get key from: https://console.groq.com/keys"
#             )
#         return v
    
#     LLM_MODEL: str = "llama-3.3-70b-versatile"
#     LLM_BASE_URL: str = "https://api.groq.com/openai/v1"
#     LLM_TEMPERATURE: float = 0.1
    
#     # ========================================================================
#     # Repository Limits
#     # ========================================================================
#     MAX_REPO_SIZE_KB: int = 100000  # 100MB
#     CLONE_TIMEOUT_SECONDS: int = 120  # 2 minutes
    
#     # ========================================================================
#     # Application Config
#     # ========================================================================
#     ENVIRONMENT: str = "development"
#     DEBUG: bool = True
    
#     CORS_ORIGINS_STR: str = "http://localhost:5173,http://localhost:3000"
    
#     @property
#     def CORS_ORIGINS(self) -> list[str]:
#         return [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",")]

#     class Config:
#         env_file = ".env"
#         extra = "ignore"


# # Validate settings on import
# try:
#     settings = Settings()
#     print("✅ Configuration validated successfully")
#     print(f"   - GitHub token: {settings.GITHUB_TOKEN[:10]}...")
#     print(f"   - Groq API key: {settings.GROQ_API_KEY[:10]}...")
#     print(f"   - Environment: {settings.ENVIRONMENT}")
# except Exception as e:
#     print(f"\n{'='*70}")
#     print("❌ CONFIGURATION ERROR")
#     print(f"{'='*70}")
#     print(str(e))
#     print(f"{'='*70}\n")
#     raise