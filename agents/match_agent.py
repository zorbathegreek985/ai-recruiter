"""
Match Agent.

Calculates semantic fit, skill match, and experience match. Existing ranking
scores remain the source of truth for compatibility with the current app.
"""
from typing import Any, Dict

from embeddings.embedding_engine import semantic_similarity
from ranking.ranking_engine import (
    compute_education_score,
    compute_experience_score,
    compute_overall_score,
    compute_projects_score,
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
    education_match = compute_education_score(
        candidate.get("education", ""),
        jd.get("education", ""),
    )
    project_match = compute_projects_score(
        candidate.get("projects", []),
        jd.get("raw_text", ""),
    )

    semantic_fit = semantic_similarity(_candidate_text(candidate), _jd_text(jd)) * 100
    scores = compute_overall_score(candidate, jd)

    return {
        "semantic_fit": round(max(0.0, min(100.0, semantic_fit)), 2),
        "skill_match": round(skill_match, 2),
        "experience_match": round(experience_match, 2),
        "education_match": round(education_match, 2),
        "project_match": round(project_match, 2),
        "explainable_scores": {
            "skill_match": scores.get("skill_match", round(skill_match, 2)),
            "experience_match": scores.get("experience", round(experience_match, 2)),
            "education_match": scores.get("education", round(education_match, 2)),
            "project_match": scores.get("projects", round(project_match, 2)),
            "semantic_fit": round(max(0.0, min(100.0, semantic_fit)), 2),
            "overall": scores.get("overall", 0),
        },
        "scores": scores,
    }
