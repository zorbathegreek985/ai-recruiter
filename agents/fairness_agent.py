"""Fairness ranking views for bias-aware recruiter review."""
from typing import Any, Dict, List


def _clone(candidate: Dict[str, Any], rank: int, score: float, mode: str) -> Dict[str, Any]:
    return {
        "rank": rank,
        "candidate": candidate.get("name", "Unknown"),
        "score": round(score, 2),
        "mode": mode,
        "skills": ", ".join(candidate.get("skills", [])[:6]),
        "risk": candidate.get("risk_report", {}).get("risk_level", "Low"),
    }


def _rank_by(candidates: List[Dict[str, Any]], mode: str, score_fn) -> List[Dict[str, Any]]:
    scored = sorted(candidates, key=score_fn, reverse=True)
    return [_clone(candidate, idx, score_fn(candidate), mode) for idx, candidate in enumerate(scored, 1)]


def build_fairness_dashboard(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create skill-only, name-blind, and education-blind ranking views."""
    skill_only = _rank_by(
        candidates,
        "Skill-only",
        lambda c: c.get("scores", {}).get("skill_match", 0),
    )
    name_blind = _rank_by(
        candidates,
        "Name-blind",
        lambda c: c.get("overall_score", c.get("scores", {}).get("overall", 0)),
    )
    education_blind = _rank_by(
        candidates,
        "Education-blind",
        lambda c: (
            c.get("scores", {}).get("skill_match", 0) * 0.55
            + c.get("scores", {}).get("experience", 0) * 0.30
            + c.get("scores", {}).get("projects", 0) * 0.15
        ),
    )

    original_top = [c.get("name", "Unknown") for c in sorted(candidates, key=lambda c: c.get("rank", 999))]
    skill_top = [row["candidate"] for row in skill_only]
    education_top = [row["candidate"] for row in education_blind]

    top3_original = set(original_top[:3])
    skill_overlap = len(top3_original & set(skill_top[:3]))
    education_overlap = len(top3_original & set(education_top[:3]))
    bias_flags = sum(len(c.get("bias_report", {}).get("signals", [])) for c in candidates)

    return {
        "skill_only": skill_only,
        "name_blind": name_blind,
        "education_blind": education_blind,
        "metrics": {
            "top3_skill_overlap": skill_overlap,
            "top3_education_blind_overlap": education_overlap,
            "bias_signal_count": bias_flags,
            "review_status": "Needs Review" if bias_flags else "Low Bias Signal",
        },
        "guidance": [
            "Compare whether the same candidates remain competitive when education is removed.",
            "Prioritize skill evidence, project ownership, and role-relevant experience.",
            "Use bias flags as review prompts, not as automatic rejection criteria.",
        ],
    }
