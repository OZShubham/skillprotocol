"""
GitHub Tools
Helper functions for interacting with GitHub API
"""

import httpx
from typing import Dict, Optional, List
from app.core.config import settings


class GitHubClient:
    """
    Wrapper for GitHub REST API
    Handles authentication and common operations
    """
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.GITHUB_TOKEN
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    async def get_repo_info(self, owner: str, repo: str) -> Optional[Dict]:
        """
        Get repository metadata
        
        Returns:
            {
                "name": "repo-name",
                "size": 12345,  # KB
                "language": "Python",
                "stargazers_count": 100,
                "fork": false,
                ...
            }
        """
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo}",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    return response.json()
                
                return None
                
            except Exception as e:
                print(f"Error fetching repo info: {str(e)}")
                return None
    
    async def check_file_exists(self, owner: str, repo: str, filepath: str) -> bool:
        """
        Check if a specific file exists in the repository
        
        Example:
            exists = await client.check_file_exists("user", "repo", "README.md")
        """
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/contents/{filepath}",
                    headers=self.headers
                )
                
                return response.status_code == 200
                
            except:
                return False
    
    async def get_workflow_runs(
        self, 
        owner: str, 
        repo: str,
        status: str = "completed",
        per_page: int = 5
    ) -> List[Dict]:
        """
        Get GitHub Actions workflow runs
        
        Args:
            owner: Repository owner
            repo: Repository name
            status: "completed", "in_progress", "queued"
            per_page: Number of results
            
        Returns:
            List of workflow run objects
        """
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/actions/runs",
                    headers=self.headers,
                    params={
                        "status": status,
                        "per_page": per_page
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("workflow_runs", [])
                
                return []
                
            except Exception as e:
                print(f"Error fetching workflow runs: {str(e)}")
                return []
    
    async def get_latest_commit(self, owner: str, repo: str) -> Optional[Dict]:
        """
        Get the latest commit on default branch
        """
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/commits",
                    headers=self.headers,
                    params={"per_page": 1}
                )
                
                if response.status_code == 200:
                    commits = response.json()
                    return commits[0] if commits else None
                
                return None
                
            except Exception as e:
                print(f"Error fetching latest commit: {str(e)}")
                return None
    
    async def get_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """
        Get programming languages used in the repository
        
        Returns:
            {"Python": 12345, "JavaScript": 5678}  # Bytes per language
        """
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/languages",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    return response.json()
                
                return {}
                
            except Exception as e:
                print(f"Error fetching languages: {str(e)}")
                return {}
    
    async def get_rate_limit(self) -> Dict:
        """
        Check GitHub API rate limit status
        
        Returns:
            {
                "limit": 5000,
                "remaining": 4999,
                "reset": 1234567890  # Unix timestamp
            }
        """
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/rate_limit",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("rate", {}).get("core", {})
                
                return {}
                
            except Exception as e:
                print(f"Error checking rate limit: {str(e)}")
                return {}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_github_url(url: str) -> Optional[tuple[str, str]]:
    """
    Parse GitHub URL to extract owner and repo name
    
    Args:
        url: "https://github.com/user/repo" or "https://github.com/user/repo.git"
        
    Returns:
        ("user", "repo") or None if invalid
    """
    
    # Remove .git suffix
    url = url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    
    # Extract owner and repo
    parts = url.replace("https://github.com/", "").split("/")
    
    if len(parts) >= 2:
        return parts[0], parts[1]
    
    return None


async def validate_github_token(token: str) -> bool:
    """
    Validate that a GitHub token is valid and has correct permissions
    
    Returns:
        True if token is valid, False otherwise
    """
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(
                "https://api.github.com/user",
                headers=headers
            )
            
            return response.status_code == 200
            
        except:
            return False


async def check_repo_accessibility(repo_url: str, token: str) -> Dict:
    """
    Check if a repository is accessible with the given token
    
    Returns:
        {
            "accessible": True/False,
            "is_private": True/False,
            "exists": True/False,
            "error": "error message" (if any)
        }
    """
    
    parsed = parse_github_url(repo_url)
    if not parsed:
        return {
            "accessible": False,
            "exists": False,
            "error": "Invalid GitHub URL"
        }
    
    owner, repo = parsed
    
    client = GitHubClient(token)
    repo_info = await client.get_repo_info(owner, repo)
    
    if not repo_info:
        return {
            "accessible": False,
            "exists": False,
            "error": "Repository not found or private"
        }
    
    return {
        "accessible": True,
        "exists": True,
        "is_private": repo_info.get("private", False),
        "error": None
    }