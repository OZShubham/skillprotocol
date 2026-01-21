"""
Git History Analyzer
Extracts stability metrics from repository history
"""

import subprocess
from pathlib import Path
from typing import Optional


class GitAnalyzer:
    """Analyzes git history to determine repository stability"""
    
    def analyze_stability(self, repo_path: str) -> float:
        """
        Calculate git stability score (0-1)
        
        Methodology:
        - Consistent commit patterns → high stability
        - Erratic/bursty commits → low stability
        
        Returns:
            0-1 score (0.5 = neutral if no git history)
        """
        
        if not (Path(repo_path) / ".git").exists():
            return 0.5  # Neutral prior for non-git repos
        
        try:
            # Count total commits
            commits = self._get_commit_count(repo_path)
            
            if commits == 0:
                return 0.3  # Very unstable (new repo)
            
            # Get commit dates
            dates = self._get_commit_dates(repo_path)
            
            if not dates:
                return 0.5
            
            # Calculate active days
            unique_days = len(set(dates))
            
            if unique_days == 0:
                return 0.5
            
            # Average commits per day
            avg_commits_per_day = commits / unique_days
            
            # Stability curve:
            # 1-2 commits/day = stable (0.8-0.9)
            # 3-5 commits/day = moderate (0.6-0.7)
            # 10+ commits/day = thrashing (0.3-0.4)
            
            if avg_commits_per_day < 1.0:
                # Slow development
                stability = 0.7 + (avg_commits_per_day * 0.2)
            elif avg_commits_per_day < 3.0:
                # Ideal cadence
                stability = 0.85
            else:
                # Excessive churn
                stability = 1.0 / (1.0 + 0.1 * (avg_commits_per_day - 2.0))
            
            return round(min(0.95, max(0.2, stability)), 2)
            
        except Exception as e:
            print(f"⚠️ Git analysis failed: {str(e)}")
            return 0.5  # Neutral fallback
    
    def _get_commit_count(self, repo_path: str) -> int:
        """Get total number of commits"""
        try:
            result = subprocess.check_output(
                ["git", "-C", repo_path, "rev-list", "--count", "HEAD"],
                stderr=subprocess.DEVNULL,
                timeout=5
            )
            return int(result.decode().strip())
        except Exception:
            return 0
    
    def _get_commit_dates(self, repo_path: str) -> list:
        """Get list of commit dates (YYYY-MM-DD)"""
        try:
            result = subprocess.check_output(
                ["git", "-C", repo_path, "log", "--pretty=format:%ai"],
                stderr=subprocess.DEVNULL,
                timeout=5
            )
            
            log = result.decode()
            dates = [line.split()[0] for line in log.splitlines() if line.strip()]
            
            return dates
            
        except Exception:
            return []


# Singleton
_git_analyzer_instance = None

def get_git_analyzer() -> GitAnalyzer:
    """Get singleton instance"""
    global _git_analyzer_instance
    if _git_analyzer_instance is None:
        _git_analyzer_instance = GitAnalyzer()
    return _git_analyzer_instance