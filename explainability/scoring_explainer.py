"""Transparent score cards for explainable recruiting decisions."""
from typing import Any, Dict, List


SCORE_WEIGHTS = {
    "skill_match": 0.45,
    "experience": 0.30,
    "projects": 0.15,
    "education": 0.10,
}


def build_score_evidence(candidate: Dict[str, Any], jd: Dict[str, Any]) -> Dict[str, Any]:
    """Explain how each score dimension was supported by extracted evidence."""
    scores = candidate.get("scores", {})
    candidate_skills = {skill.lower(): skill for skill in candidate.get("skills", [])}
    required = jd.get("required_skills", [])
    preferred = jd.get("preferred_skills", [])

    matched_required = [skill for skill in required if skill.lower() in candidate_skills]
    missing_required = [skill for skill in required if skill.lower() not in candidate_skills]
    matched_preferred = [skill for skill in preferred if skill.lower() in candidate_skills]

    dimensions: List[Dict[str, Any]] = [
        {
            "dimension": "Skill Match",
            "score": scores.get("skill_match", 0),
            "weight": SCORE_WEIGHTS["skill_match"],
            "evidence": [
                "Matched required skills: " + (", ".join(matched_required) or "None"),
                "Matched preferred skills: " + (", ".join(matched_preferred) or "None"),
                "Missing required skills: " + (", ".join(missing_required) or "None"),
            ],
        },
        {
            "dimension": "Experience",
            "score": scores.get("experience", 0),
            "weight": SCORE_WEIGHTS["experience"],
            "evidence": [
                f"Candidate experience: {candidate.get('experience_years', 0)} years",
                f"JD requirement: {jd.get('experience', 'Not specified')}",
            ],
        },
        {
            "dimension": "Projects",
            "score": scores.get("projects", 0),
            "weight": SCORE_WEIGHTS["projects"],
            "evidence": candidate.get("projects", [])[:4] or ["No project evidence extracted"],
        },
        {
            "dimension": "Education",
            "score": scores.get("education", 0),
            "weight": SCORE_WEIGHTS["education"],
            "evidence": [candidate.get("education", "Not specified")],
        },
        {
            "dimension": "Risk",
            "score": candidate.get("risk_report", {}).get("risk_score", 0),
            "weight": 0,
            "evidence": [
                f"Risk level: {candidate.get('risk_report', {}).get('risk_level', 'Low')}",
                "Signals: "
                + (
                    ", ".join(candidate.get("hiring_recommendation", {}).get("risks", [])[:4])
                    or "No major risk signals detected"
                ),
            ],
        },
    ]

    contribution_total = 0.0
    for item in dimensions:
        item["weighted_contribution"] = round(item["score"] * item["weight"], 2)
        contribution_total += item["weighted_contribution"]

    return {
        "candidate": candidate.get("name", "Unknown"),
        "overall": candidate.get("overall_score", scores.get("overall", round(contribution_total, 2))),
        "dimensions": dimensions,
        "decision_factors": candidate.get("hiring_recommendation", {}),
    }
