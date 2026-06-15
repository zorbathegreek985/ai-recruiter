"""Recruiter dashboard helpers for batch analytics and decision tables."""
from collections import Counter
from typing import Any, Dict, List

import pandas as pd


def build_batch_summary(ranked_candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate candidate batch health for recruiter dashboards."""
    if not ranked_candidates:
        return {
            "total": 0,
            "strong_hires": 0,
            "interview_ready": 0,
            "needs_review": 0,
            "avg_score": 0,
            "avg_risk": 0,
            "top_missing_skills": [],
        }

    recommendations = Counter(
        c.get("hiring_recommendation", {}).get("recommendation", "Unclassified")
        for c in ranked_candidates
    )
    missing = Counter()
    risks = []
    for candidate in ranked_candidates:
        risks.append(candidate.get("risk_report", {}).get("risk_score", 0))
        for skill in candidate.get("hiring_recommendation", {}).get("missing_skills", []):
            missing[skill] += 1

    return {
        "total": len(ranked_candidates),
        "strong_hires": recommendations.get("Strong Hire", 0),
        "interview_ready": recommendations.get("Interview", 0),
        "needs_review": (
            recommendations.get("Consider", 0)
            + recommendations.get("Reject", 0)
            + recommendations.get("Review Manually", 0)
            + recommendations.get("Maybe", 0)
        ),
        "avg_score": round(sum(c.get("overall_score", 0) for c in ranked_candidates) / len(ranked_candidates), 1),
        "avg_risk": round(sum(risks) / len(risks), 1) if risks else 0,
        "top_missing_skills": missing.most_common(5),
    }


def build_candidate_decision_table(ranked_candidates: List[Dict[str, Any]]) -> pd.DataFrame:
    """Return a recruiter-facing decision table."""
    rows = []
    for candidate in ranked_candidates:
        hiring = candidate.get("hiring_recommendation", {})
        risk = candidate.get("risk_report", {})
        scores = candidate.get("scores", {})
        rows.append(
            {
                "Rank": candidate.get("rank"),
                "Candidate": candidate.get("name", "Unknown"),
                "Decision": hiring.get("recommendation", "Review"),
                "Overall": candidate.get("overall_score", scores.get("overall", 0)),
                "Skill Match": scores.get("skill_match", 0),
                "Experience": scores.get("experience", 0),
                "Risk": risk.get("risk_level", "Low"),
                "Missing Skills": ", ".join(hiring.get("missing_skills", [])[:4]),
            }
        )
    return pd.DataFrame(rows)


def filter_candidates(
    ranked_candidates: List[Dict[str, Any]],
    query: str = "",
    min_score: float = 0,
    max_risk: str = "High",
    recommendation: str = "All",
) -> List[Dict[str, Any]]:
    """Filter candidates by recruiter-facing criteria."""
    risk_rank = {"Low": 1, "Medium": 2, "High": 3}
    max_risk_value = risk_rank.get(max_risk, 3)
    query_lower = (query or "").lower().strip()
    filtered = []

    for candidate in ranked_candidates:
        text = " ".join(
            [
                candidate.get("name", ""),
                " ".join(candidate.get("skills", [])),
                " ".join(candidate.get("projects", [])),
                candidate.get("education", ""),
            ]
        ).lower()
        candidate_recommendation = candidate.get("hiring_recommendation", {}).get("recommendation", "Review")
        candidate_risk = candidate.get("risk_report", {}).get("risk_level", "Low")

        if query_lower and query_lower not in text:
            continue
        if candidate.get("overall_score", 0) < min_score:
            continue
        if risk_rank.get(candidate_risk, 1) > max_risk_value:
            continue
        if recommendation != "All" and candidate_recommendation != recommendation:
            continue
        filtered.append(candidate)

    return filtered


def sort_candidates(ranked_candidates: List[Dict[str, Any]], sort_by: str = "Overall") -> List[Dict[str, Any]]:
    """Sort candidates by a visible dashboard dimension."""
    sort_map = {
        "Overall": lambda c: c.get("overall_score", 0),
        "Skill Match": lambda c: c.get("scores", {}).get("skill_match", 0),
        "Experience": lambda c: c.get("scores", {}).get("experience", 0),
        "Projects": lambda c: c.get("scores", {}).get("projects", 0),
        "Education": lambda c: c.get("scores", {}).get("education", 0),
        "Lowest Risk": lambda c: -c.get("risk_report", {}).get("risk_score", 0),
    }
    key = sort_map.get(sort_by, sort_map["Overall"])
    return sorted(ranked_candidates, key=key, reverse=True)


def compare_candidates(candidates: List[Dict[str, Any]]) -> pd.DataFrame:
    """Create a side-by-side comparison table for selected candidates."""
    rows = []
    for candidate in candidates:
        scores = candidate.get("scores", {})
        hiring = candidate.get("hiring_recommendation", {})
        gaps = candidate.get("advanced_skill_gap", {})
        rows.append(
            {
                "Candidate": candidate.get("name", "Unknown"),
                "Overall": candidate.get("overall_score", 0),
                "Skill Match": scores.get("skill_match", 0),
                "Experience": scores.get("experience", 0),
                "Projects": scores.get("projects", 0),
                "Education": scores.get("education", 0),
                "Recommendation": hiring.get("recommendation", "Review"),
                "Strengths": "; ".join(hiring.get("strengths", [])[:3]),
                "Missing Skills": ", ".join(gaps.get("missing_skills", hiring.get("missing_skills", []))[:5]),
            }
        )
    return pd.DataFrame(rows)
