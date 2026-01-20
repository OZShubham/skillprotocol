"""
Validator Agent - FIXED
Fixes the 'rstrip' bug that corrupted repository names ending in g, i, or t.
"""

import httpx
import re
from typing import Dict, Any, Optional
from app.core.state import AnalysisState, get_progress_for_step
from app.core.config import settings
from app.core.opik_config import track_agent

@track_agent(
    name="Validator Agent",
    agent_type="tool",
    tags=["validation", "agent"]
)
async def validate_repository(state: AnalysisState) -> AnalysisState:
    """
    Agent 1: Validator (FIXED)
    """
    
    # Update progress
    state["current_step"] = "validator"
    state["progress"] = get_progress_for_step("validator")
    
    print(f"🔍 [Validator Agent] Starting validation for: {state['repo_url']}")
    
    try:
        # ====================================================================
        # STEP 1: VALIDATE GITHUB URL FORMAT
        # ====================================================================
        repo_url = state["repo_url"].strip()
        
        # Regex for GitHub URLs
        github_pattern = r'^(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+?)(?:\.git)?/?$'
        
        match = re.match(github_pattern, repo_url)
        
        if not match:
            error_msg = "Invalid GitHub URL. Expected format: https://github.com/owner/repo"
            print(f"❌ [Validator Agent] {error_msg}")
            state["errors"].append(error_msg)
            state["should_skip"] = True
            state["skip_reason"] = "Invalid URL format"
            state["validation"] = {
                "is_valid": False,
                "error": error_msg,
                "error_type": "INVALID_URL"
            }
            return state
        
        owner, repo_name = match.groups()
        
        # --- FIX STARTS HERE ---
        # OLD (BUGGY): repo_name = repo_name.rstrip('.git')
        # NEW (CORRECT): Use removesuffix to only remove the exact substring
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4] 
        # Alternatively in Python 3.9+: repo_name = repo_name.removesuffix('.git')
        # --- FIX ENDS HERE ---
        
        print(f"✅ [Validator Agent] Parsed URL: {owner}/{repo_name}")
        
        # ====================================================================
        # STEP 2: CHECK REPO ACCESSIBILITY
        # ====================================================================
        headers = {
            "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo_name}",
                headers=headers
            )
            
            # HANDLE 404 - Could be private or non-existent
            if response.status_code == 404:
                # Check if user provided a token
                user_token = state.get("user_github_token")
                
                if user_token:
                    print(f"🔓 [Validator Agent] Trying user token for private repo...")
                    user_headers = {
                        "Authorization": f"Bearer {user_token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                    
                    user_response = await client.get(
                        f"https://api.github.com/repos/{owner}/{repo_name}",
                        headers=user_headers
                    )
                    
                    if user_response.status_code == 200:
                        repo_data = user_response.json()
                        print(f"✅ [Validator Agent] Private repo accessible with user token")
                        state["validation"] = {
                            "is_valid": True,
                            "is_private": True,
                            "owner": owner,
                            "repo_name": repo_name,
                            "requires_user_token": True,
                            # Populate minimal data to avoid crashes downstream if we skip full metadata
                            "size_kb": repo_data.get("size", 0),
                            "language": repo_data.get("language", "Unknown"),
                            "markers": {"has_readme": False} # Will be updated by scanner
                        }
                        # We continue to standard flow to populate full data
                        response = user_response 
                    else:
                        error_msg = "Invalid GitHub token or no access to this private repository"
                        print(f"❌ [Validator Agent] {error_msg}")
                        state["errors"].append(error_msg)
                        state["should_skip"] = True
                        state["skip_reason"] = "Token invalid or insufficient permissions"
                        state["validation"] = {
                            "is_valid": False,
                            "error": error_msg,
                            "error_type": "TOKEN_INVALID"
                        }
                        return state
                else:
                    # No token provided - assume private
                    error_msg = f"Repository '{owner}/{repo_name}' not found or is private. Please provide a GitHub token."
                    print(f"🔒 [Validator Agent] {error_msg}")
                    state["errors"].append(error_msg)
                    state["should_skip"] = True
                    state["skip_reason"] = "Private repo - token required"
                    state["validation"] = {
                        "is_valid": False,
                        "error": error_msg,
                        "error_type": "PRIVATE_REPO",
                        "owner": owner,
                        "repo_name": repo_name
                    }
                    return state
            
            # HANDLE RATE LIMIT
            elif response.status_code == 403:
                error_msg = "GitHub API rate limit exceeded. Please try again later."
                print(f"⚠️  [Validator Agent] {error_msg}")
                state["errors"].append(error_msg)
                state["should_skip"] = True
                state["skip_reason"] = "Rate limit exceeded"
                state["validation"] = {
                    "is_valid": False,
                    "error": error_msg,
                    "error_type": "RATE_LIMIT"
                }
                return state
            
            # HANDLE OTHER ERRORS
            elif response.status_code != 200:
                error_msg = f"GitHub API error: {response.status_code}"
                print(f"❌ [Validator Agent] {error_msg}")
                state["errors"].append(error_msg)
                state["should_skip"] = True
                state["skip_reason"] = "GitHub API error"
                state["validation"] = {
                    "is_valid": False,
                    "error": error_msg,
                    "error_type": "API_ERROR"
                }
                return state
            
            # Success
            repo_data = response.json()
        
        # ====================================================================
        # STEP 3: EXTRACT METADATA & VALIDATE SIZE
        # ====================================================================
        size_kb = repo_data.get("size", 0)
        language = repo_data.get("language", "Unknown")
        stars = repo_data.get("stargazers_count", 0)
        is_fork = repo_data.get("fork", False)
        is_private = repo_data.get("private", False)
        
        # Check size limit
        if size_kb > settings.MAX_REPO_SIZE_KB:
            error_msg = f"Repository too large ({size_kb} KB). Maximum allowed: {settings.MAX_REPO_SIZE_KB} KB"
            print(f"❌ [Validator Agent] {error_msg}")
            state["errors"].append(error_msg)
            state["should_skip"] = True
            state["skip_reason"] = f"Repo size exceeds limit"
            state["validation"] = {
                "is_valid": False,
                "error": error_msg,
                "error_type": "SIZE_EXCEEDED",
                "size_kb": size_kb
            }
            return state
        
        # Check if repo is empty
        if size_kb == 0:
            error_msg = "Repository appears to be empty"
            print(f"⚠️  [Validator Agent] {error_msg}")
            state["errors"].append(error_msg)
            state["should_skip"] = True
            state["skip_reason"] = "Empty repository"
            state["validation"] = {
                "is_valid": False,
                "error": error_msg,
                "error_type": "EMPTY_REPO"
            }
            return state
        
        # ====================================================================
        # STEP 4: DETECT SFIA MARKERS (Quick API Check)
        # ====================================================================
        print(f"🏷️  [Validator Agent] Detecting SFIA markers...")
        
        # Determine token for API calls
        marker_headers = headers.copy()
        if is_private and state.get("user_github_token"):
            marker_headers["Authorization"] = f"Bearer {state.get('user_github_token')}"

        markers = await _detect_quick_markers(
            owner, 
            repo_name, 
            marker_headers, 
            httpx.AsyncClient()
        )
        
        # ====================================================================
        # STEP 5: BUILD VALIDATION RESULT
        # ====================================================================
        validation_result = {
            "is_valid": True,
            "is_private": is_private,
            "owner": owner,
            "repo_name": repo_name,
            "size_kb": size_kb,
            "language": language,
            "stars": stars,
            "is_fork": is_fork,
            "markers": markers,
            "requires_user_token": is_private
        }
        
        state["validation"] = validation_result
        
        print(f"✅ [Validator Agent] Validation PASSED:")
        print(f"   - Repo: {owner}/{repo_name}")
        print(f"   - Size: {size_kb} KB")
        print(f"   - Language: {language}")
        print(f"   - Private: {is_private}")
        print(f"   - Has README: {markers['has_readme']}")
        
        return state
        
    except httpx.TimeoutException:
        error_msg = "GitHub request timed out. Please try again."
        print(f"⏱️  [Validator Agent] {error_msg}")
        state["errors"].append(error_msg)
        state["should_skip"] = True
        state["skip_reason"] = "Request timeout"
        state["validation"] = {
            "is_valid": False,
            "error": error_msg,
            "error_type": "TIMEOUT"
        }
        return state
        
    except Exception as e:
        error_msg = f"Validation error: {str(e)}"
        print(f"❌ [Validator Agent] {error_msg}")
        state["errors"].append(error_msg)
        state["should_skip"] = True
        state["skip_reason"] = "Validation exception"
        state["validation"] = {
            "is_valid": False,
            "error": error_msg,
            "error_type": "UNKNOWN"
        }
        return state


async def _detect_quick_markers(
    owner: str, 
    repo_name: str, 
    headers: Dict[str, str],
    client: httpx.AsyncClient
) -> Dict[str, bool]:
    """
    Detect SFIA markers without cloning (just API calls)
    """
    
    markers = {
        "has_readme": False,
        "has_requirements": False,
        "has_ci_cd": False,
        "has_docker": False
    }
    
    # Check for README
    for readme_name in ["README.md", "readme.md", "README.rst", "README.txt"]:
        try:
            resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo_name}/contents/{readme_name}",
                headers=headers,
                timeout=5.0
            )
            if resp.status_code == 200:
                markers["has_readme"] = True
                break
        except:
            pass
    
    # Check for requirements
    for req_file in ["requirements.txt", "package.json", "go.mod", "Cargo.toml", "pom.xml", "pyproject.toml"]:
        try:
            resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo_name}/contents/{req_file}",
                headers=headers,
                timeout=5.0
            )
            if resp.status_code == 200:
                markers["has_requirements"] = True
                break
        except:
            pass
    
    # Check for CI/CD
    try:
        resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo_name}/contents/.github/workflows",
            headers=headers,
            timeout=5.0
        )
        if resp.status_code == 200:
            markers["has_ci_cd"] = True
    except:
        pass
    
    # Check for Docker
    try:
        resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo_name}/contents/Dockerfile",
            headers=headers,
            timeout=5.0
        )
        if resp.status_code == 200:
            markers["has_docker"] = True
    except:
        pass
    
    return markers