"""GitHub Profile Analyzer with optional live public API lookup."""
import json
import re
import urllib.request
from typing import Any, Dict, Optional


GITHUB_RE = re.compile(r"github\.com/([A-Za-z0-9-]+)", re.IGNORECASE)


def extract_github_username(text: str) -> Optional[str]:
    match = GITHUB_RE.search(text or "")
    return match.group(1) if match else None


def analyze_github_profile(candidate: Dict[str, Any], timeout: int = 4) -> Dict[str, Any]:
    """Analyze public GitHub activity if a profile URL is present."""
    username = extract_github_username(candidate.get("raw_text", ""))
    if not username:
        return {
            "username": None,
            "available": False,
            "summary": "No GitHub profile found in resume text.",
            "signals": [],
            "score": 0,
        }

    url = f"https://api.github.com/users/{username}/repos?per_page=20&sort=updated"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            repos = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {
            "username": username,
            "available": False,
            "summary": f"GitHub username found, but live profile analysis was unavailable: {exc}",
            "signals": ["Profile URL detected in resume"],
            "score": 20,
        }

    languages = {}
    stars = 0
    relevant_repos = []
    for repo in repos:
        lang = repo.get("language")
        if lang:
            languages[lang] = languages.get(lang, 0) + 1
        stars += repo.get("stargazers_count", 0) or 0
        name_desc = f"{repo.get('name', '')} {repo.get('description', '') or ''}".lower()
        if any(term in name_desc for term in ["ai", "ml", "machine-learning", "rag", "nlp", "data", "model"]):
            relevant_repos.append(repo.get("name", "repo"))

    score = min(100, 25 + len(repos) * 2 + min(25, stars) + len(relevant_repos) * 8)
    top_languages = sorted(languages.items(), key=lambda item: item[1], reverse=True)[:5]

    return {
        "username": username,
        "available": True,
        "summary": f"Analyzed {len(repos)} recent repositories for @{username}.",
        "signals": [
            f"Top languages: {', '.join(lang for lang, _ in top_languages) or 'None detected'}",
            f"Relevant AI/data repositories: {', '.join(relevant_repos[:5]) or 'None detected'}",
            f"Total stars across recent repos: {stars}",
        ],
        "score": score,
    }
