"""
Private Repository Handler
Manages authentication and access for private GitHub repositories
"""

import httpx
from typing import Optional, Dict
from app.core.config import settings


async def check_repo_access(repo_url: str, user_github_token: Optional[str] = None) -> Dict:
    """
    Check if we can access a repository (public or private)
    
    Args:
        repo_url: GitHub repository URL
        user_github_token: Optional user-provided GitHub token for private repos
        
    Returns:
        {
            "accessible": bool,
            "is_private": bool,
            "requires_auth": bool,
            "error": str or None
        }
    """
    
    # Parse owner and repo from URL
    parts = repo_url.replace("https://github.com/", "").replace(".git", "").split("/")
    if len(parts) < 2:
        return {
            "accessible": False,
            "is_private": False,
            "requires_auth": False,
            "error": "Invalid GitHub URL"
        }
    
    owner, repo = parts[0], parts[1]
    
    # Try with app's default token first (works for public repos)
    headers = {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers=headers
        )
        
        # Public repo - accessible with app token
        if response.status_code == 200:
            data = response.json()
            return {
                "accessible": True,
                "is_private": data.get("private", False),
                "requires_auth": False,
                "error": None
            }
        
        # 404 could mean: repo doesn't exist OR it's private and we don't have access
        if response.status_code == 404:
            
            # If user provided their own token, try with that
            if user_github_token:
                user_headers = {
                    "Authorization": f"Bearer {user_github_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                
                user_response = await client.get(
                    f"https://api.github.com/repos/{owner}/{repo}",
                    headers=user_headers
                )
                
                if user_response.status_code == 200:
                    data = user_response.json()
                    return {
                        "accessible": True,
                        "is_private": data.get("private", False),
                        "requires_auth": True,  # User token was needed
                        "error": None
                    }
            
            # Couldn't access - either doesn't exist or is private without access
            return {
                "accessible": False,
                "is_private": True,  # Assume private
                "requires_auth": True,
                "error": "Repository not found or private. Please provide a GitHub token with access."
            }
        
        # Other errors (rate limit, server error, etc.)
        return {
            "accessible": False,
            "is_private": False,
            "requires_auth": False,
            "error": f"GitHub API error: {response.status_code}"
        }


def get_clone_url_with_auth(repo_url: str, token: str) -> str:
    """
    Convert a regular GitHub URL to an authenticated clone URL
    
    Args:
        repo_url: https://github.com/user/repo
        token: GitHub personal access token
        
    Returns:
        https://x-access-token:TOKEN@github.com/user/repo
    """
    
    # Remove existing protocol
    url = repo_url.replace("https://", "").replace("http://", "")
    
    # Add token authentication
    auth_url = f"https://x-access-token:{token}@{url}"
    
    # Remove .git if present (will be added by git.Repo.clone_from)
    return auth_url.replace(".git", "")


async def validate_user_github_token(token: str) -> Dict:
    """
    Validate that a user's GitHub token is valid and has correct scopes
    
    Args:
        token: User's GitHub personal access token
        
    Returns:
        {
            "valid": bool,
            "username": str or None,
            "scopes": list[str],
            "error": str or None
        }
    """
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Get authenticated user info
            response = await client.get(
                "https://api.github.com/user",
                headers=headers
            )
            
            if response.status_code != 200:
                return {
                    "valid": False,
                    "username": None,
                    "scopes": [],
                    "error": "Invalid GitHub token"
                }
            
            user_data = response.json()
            
            # Check token scopes from headers
            scopes_header = response.headers.get("X-OAuth-Scopes", "")
            scopes = [s.strip() for s in scopes_header.split(",") if s.strip()]
            
            # Verify token has 'repo' scope (needed for private repos)
            has_repo_scope = "repo" in scopes or "public_repo" in scopes
            
            if not has_repo_scope:
                return {
                    "valid": False,
                    "username": user_data.get("login"),
                    "scopes": scopes,
                    "error": "Token missing 'repo' scope. Please create a new token with 'repo' access."
                }
            
            return {
                "valid": True,
                "username": user_data.get("login"),
                "scopes": scopes,
                "error": None
            }
            
        except Exception as e:
            return {
                "valid": False,
                "username": None,
                "scopes": [],
                "error": str(e)
            }


async def get_repo_with_best_token(
    repo_url: str, 
    user_token: Optional[str] = None
) -> tuple[str, bool]:
    """
    Determine which token to use for accessing a repository
    
    Args:
        repo_url: GitHub repository URL
        user_token: Optional user-provided token
        
    Returns:
        (token_to_use, is_user_token)
    """
    
    # First, check if repo is accessible with app token
    access_check = await check_repo_access(repo_url, user_token)
    
    if access_check["accessible"] and not access_check["requires_auth"]:
        # Public repo - use app token
        return settings.GITHUB_TOKEN, False
    
    if access_check["accessible"] and access_check["requires_auth"]:
        # Private repo accessible with user token
        if user_token:
            # Validate user token
            validation = await validate_user_github_token(user_token)
            if validation["valid"]:
                return user_token, True
            else:
                raise ValueError(f"Invalid user token: {validation['error']}")
        else:
            raise ValueError("Private repository requires authentication")
    
    # Not accessible
    raise ValueError(access_check.get("error", "Cannot access repository"))


# ============================================================================
# USAGE IN AGENTS
# ============================================================================

"""
EXAMPLE: In validator.py

from app.agents.private_repo_handler import check_repo_access, get_repo_with_best_token

async def validate_repository(state: AnalysisState):
    repo_url = state["repo_url"]
    user_token = state.get("user_github_token")  # From API request
    
    # Check access
    access = await check_repo_access(repo_url, user_token)
    
    if not access["accessible"]:
        state["errors"].append(access["error"])
        state["should_skip"] = True
        state["skip_reason"] = "Cannot access repository"
        return state
    
    # Store info about repo access
    state["validation"]["is_private"] = access["is_private"]
    state["validation"]["requires_user_token"] = access["requires_auth"]
    
    return state


EXAMPLE: In scanner.py

from app.agents.private_repo_handler import get_repo_with_best_token, get_clone_url_with_auth

async def scan_codebase(state: AnalysisState):
    repo_url = state["repo_url"]
    user_token = state.get("user_github_token")
    
    # Get the right token to use
    token, is_user_token = await get_repo_with_best_token(repo_url, user_token)
    
    # Create authenticated clone URL
    auth_url = get_clone_url_with_auth(repo_url, token)
    
    # Clone with authentication
    git.Repo.clone_from(auth_url, temp_dir, depth=1)
    
    # Rest of scanning logic...
"""