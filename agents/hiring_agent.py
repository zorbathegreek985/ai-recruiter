"""
Hiring Agent.

Generates recruiter-facing recommendation, confidence, strengths, weaknesses,
and missing skills from match and risk outputs.
"""
from typing import Any, Dict, List


def _missing_skills(candidate: Dict[str, Any], jd: Dict[str, Any]) -> List[str]:
    candidate_skills = {skill.lower() for skill in candidate.get("skills", [])}
    return [skill for skill in jd.get("required_skills", []) if skill.lower() not in candidate_skills]


def _strengths(candidate: Dict[str, Any], jd: Dict[str, Any], match: Dict[str, Any]) -> List[str]:
    strengths = []
    scores = match.get("scores", {})
    if match.get("skill_match", 0) >= 75:
        strengths.append("Strong alignment with required skills")
    if match.get("experience_match", 0) >= 80:
        strengths.append(f"Meets or exceeds experience requirement with {candidate.get('experience_years', 0)} years")
    if scores.get("projects", 0) >= 70:
        strengths.append("Relevant project background")
    if candidate.get("certifications"):
        strengths.append("Relevant certifications detected")

    matched_required = [
        skill
        for skill in jd.get("required_skills", [])
        if skill.lower() in {s.lower() for s in candidate.get("skills", [])}
    ]
    if matched_required:
        strengths.append("Matched skills: " + ", ".join(matched_required[:5]))

    return strengths[:5] or ["Some baseline alignment with the role"]


def _weaknesses(candidate: Dict[str, Any], jd: Dict[str, Any], match: Dict[str, Any], risk: Dict[str, Any]) -> List[str]:
    weaknesses = []
    missing = _missing_skills(candidate, jd)
    if missing:
        weaknesses.append("Missing required skills: " + ", ".join(missing[:5]))
    if match.get("experience_match", 0) < 70:
        weaknesses.append("Experience appears below the stated requirement")
    if match.get("semantic_fit", 0) < 45:
        weaknesses.append("Resume context has limited semantic overlap with the JD")
    if risk.get("risk_level") in {"Medium", "High"}:
        weaknesses.append(f"{risk.get('risk_level')} resume risk signals need recruiter review")

    return weaknesses[:5]


def _recommendation(overall: float, risk: Dict[str, Any]) -> str:
    risk_level = risk.get("risk_level", "Low")
    if risk_level == "High":
        return "Consider"
    if overall >= 80 and risk_level == "Low":
        return "Strong Hire"
    if overall >= 65:
        return "Interview"
    if overall >= 50:
        return "Consider"
    return "Reject"


def generate_hiring_recommendation(
    candidate: Dict[str, Any],
    jd: Dict[str, Any],
    match: Dict[str, Any],
    risk: Dict[str, Any],
) -> Dict[str, Any]:
    scores = match.get("scores", {})
    overall = scores.get("overall", candidate.get("overall_score", 0))
    risk_penalty = min(25, risk.get("risk_score", 0) * 0.25)
    confidence = max(0, min(100, round((overall * 0.75) + (match.get("semantic_fit", 0) * 0.25) - risk_penalty, 2)))

    missing = _missing_skills(candidate, jd)
    strengths = _strengths(candidate, jd, match)
    weaknesses = _weaknesses(candidate, jd, match, risk)
    suggestions = []
    if missing:
        suggestions.append("Validate adjacent experience for missing required skills before rejection.")
        suggestions.append("Use the skill-gap learning path for trainable candidates.")
    if match.get("project_match", match.get("scores", {}).get("projects", 0)) < 70:
        suggestions.append("Ask for concrete project metrics, deployment details, and ownership evidence.")
    if risk.get("risk_level") in {"Medium", "High"}:
        suggestions.append("Run manual resume verification before advancing.")
    if not suggestions:
        suggestions.append("Proceed to interview with a depth-focused technical validation plan.")

    risk_items = []
    if risk.get("risk_level") in {"Medium", "High"}:
        risk_items.append(f"{risk.get('risk_level')} resume risk score ({risk.get('risk_score', 0)})")
    risk_items.extend(risk.get("anomalies", {}).get("reasons", [])[:3])
    if risk.get("duplicates"):
        risk_items.append("Possible duplicate candidate profile in batch")
    if not risk_items:
        risk_items.append("No major resume risk signals detected")

    recommendation = _recommendation(overall, risk)
    recruiter_explanation = (
        f"{candidate.get('name', 'This candidate')} is classified as {recommendation} "
        f"with {confidence}% confidence. The decision is driven by an overall match of "
        f"{round(overall, 1)}%, skill alignment of {round(match.get('skill_match', 0), 1)}%, "
        f"and a {risk.get('risk_level', 'Low').lower()} risk profile."
    )

    return {
        "recommendation": recommendation,
        "confidence_score": confidence,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "risks": risk_items[:5],
        "missing_skills": missing,
        "improvement_suggestions": suggestions[:4],
        "hiring_recommendation": recommendation,
        "recruiter_explanation": recruiter_explanation,
    }
