"""
Match Agent.

Calculates semantic fit, skill match, and experience match. Existing ranking
scores remain the source of truth for compatibility with the current app.
"""
from typing import Any, Dict

from embeddings.embedding_engine import semantic_similarity
from ranking.ranking_engine import (
    compute_experience_score,
    compute_overall_score,
    compute_skill_match_score,
)


def _candidate_text(candidate: Dict[str, Any]) -> str:
    return " ".join(
        [
            candidate.get("name", ""),
            " ".join(candidate.get("skills", [])),
            " ".join(candidate.get("projects", [])),
            candidate.get("education", ""),
            candidate.get("raw_text", "")[:800],
        ]
    ).strip()


def _jd_text(jd: Dict[str, Any]) -> str:
    return " ".join(
        [
            jd.get("role_category", ""),
            " ".join(jd.get("required_skills", [])),
            " ".join(jd.get("preferred_skills", [])),
            jd.get("experience", ""),
            jd.get("raw_text", "")[:1000],
        ]
    ).strip()


def analyze_match(candidate: Dict[str, Any], jd: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate match dimensions for one candidate against one JD."""
    skill_match = compute_skill_match_score(
        candidate.get("skills", []),
        jd.get("required_skills", []),
        jd.get("preferred_skills", []),
    )
    experience_match = compute_experience_score(
        candidate.get("experience_years", 0),
        jd.get("experience", ""),
    )

    semantic_fit = semantic_similarity(_candidate_text(candidate), _jd_text(jd)) * 100
    scores = compute_overall_score(candidate, jd)

    return {
        "semantic_fit": round(max(0.0, min(100.0, semantic_fit)), 2),
        "skill_match": round(skill_match, 2),
        "experience_match": round(experience_match, 2),
        "scores": scores,
    }
