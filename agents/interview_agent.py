"""AI Interview Agent for recruiter-ready interview kits."""
from typing import Any, Dict, List, Optional


def _round_type(score: float) -> str:
    if score >= 80:
        return "validation"
    if score >= 60:
        return "deep-dive"
    return "gap-check"


def generate_interview_plan(
    candidate: Dict[str, Any],
    jd: Dict[str, Any],
    gaps: Optional[Dict[str, Any]] = None,
    num_questions: int = 8,
) -> Dict[str, Any]:
    """Build a structured interview plan without requiring an LLM."""
    scores = candidate.get("scores", {})
    gaps = gaps or {}
    missing = gaps.get("missing_skills") or candidate.get("hiring_recommendation", {}).get("missing_skills", [])
    matched = gaps.get("matched_skills") or []
    skills = candidate.get("skills", [])
    projects = candidate.get("projects", [])

    focus_areas = []
    if scores.get("skill_match", 0) < 75:
        focus_areas.append("Validate required skills and practical depth")
    if scores.get("projects", 0) < 70:
        focus_areas.append("Probe project ownership and production impact")
    if scores.get("experience", 0) < 75:
        focus_areas.append("Check readiness for the role seniority")
    if missing:
        focus_areas.append("Assess ability to close missing skill gaps")
    if not focus_areas:
        focus_areas.append("Confirm depth behind strong resume signals")

    primary_skill = (jd.get("required_skills") or skills or ["the core stack"])[0]
    project = (projects or ["a relevant project"])[0]
    role = jd.get("role_category", "the role")

    questions: List[Dict[str, str]] = [
        {
            "type": "Technical",
            "question": f"Walk through a production problem where you used {primary_skill}. What tradeoffs did you make?",
            "signal": "Hands-on technical depth",
        },
        {
            "type": "Project",
            "question": f"Explain your work on {project}. What was your contribution and measurable outcome?",
            "signal": "Ownership and evidence",
        },
        {
            "type": "System Design",
            "question": f"Design an end-to-end system for {role}, including deployment, monitoring, and failure modes.",
            "signal": "Architecture maturity",
        },
        {
            "type": "Problem Solving",
            "question": "How would you debug an AI workflow whose offline metrics look good but user outcomes are poor?",
            "signal": "Evaluation and debugging judgment",
        },
        {
            "type": "Collaboration",
            "question": "Tell us about a time you aligned product, data, and engineering teams around an AI deliverable.",
            "signal": "Delivery and communication",
        },
    ]

    for skill in missing[:4]:
        questions.append(
            {
                "type": "Gap Validation",
                "question": f"The JD requires {skill}. What adjacent experience do you have, and how would you ramp up in 30 days?",
                "signal": "Coachability and transferability",
            }
        )

    for skill in matched[:3]:
        questions.append(
            {
                "type": "Depth Check",
                "question": f"You listed {skill}. Describe the hardest bug or tradeoff you faced while using it.",
                "signal": "Evidence beyond keyword matching",
            }
        )

    overall = candidate.get("overall_score", scores.get("overall", 0))
    return {
        "candidate": candidate.get("name", "Unknown"),
        "recommended_round": _round_type(overall),
        "focus_areas": focus_areas,
        "questions": questions[: max(3, num_questions)],
        "question_groups": {
            "technical": [q for q in questions if q["type"] in {"Technical", "System Design", "Depth Check"}],
            "behavioral": [q for q in questions if q["type"] == "Collaboration"],
            "role_specific": [q for q in questions if q["type"] in {"Project", "Problem Solving", "Gap Validation"}],
        },
        "scoring_rubric": [
            {"criterion": "Technical depth", "excellent": "Explains tradeoffs and failure modes", "concern": "Only names tools"},
            {"criterion": "Project ownership", "excellent": "Gives measurable personal impact", "concern": "Vague team-level claims"},
            {"criterion": "Role alignment", "excellent": "Maps experience directly to JD outcomes", "concern": "Cannot connect work to role needs"},
            {"criterion": "Communication clarity", "excellent": "Structured, precise answers", "concern": "Unclear or evasive answers"},
            {"criterion": "Learning agility", "excellent": "Clear ramp-up strategy for gaps", "concern": "No plan to close gaps"},
        ],
        "red_flags_to_check": [
            "Cannot explain claimed projects in detail",
            "Over-relies on tool names without architecture reasoning",
            "No clear examples of deployment, evaluation, or iteration",
        ],
        "interview_summary": (
            f"Use a {_round_type(overall)} interview for {candidate.get('name', 'this candidate')}. "
            f"Prioritize {', '.join(focus_areas[:2]).lower()}."
        ),
    }
