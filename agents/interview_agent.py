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
    secondary_skill = (jd.get("required_skills") or skills or ["the core stack"])[1:2] or [primary_skill]
    project = (projects or ["a relevant project"])[0]
    role = jd.get("role_category", "the role")

    technical_questions: List[Dict[str, str]] = [
        {
            "type": "Technical",
            "question": f"Walk through a production problem where you used {primary_skill}. What tradeoffs did you make?",
            "signal": "Hands-on technical depth",
        },
        {
            "type": "Technical",
            "question": f"How would you evaluate model or system quality for a {role} workflow?",
            "signal": "Evaluation maturity",
        },
        {
            "type": "Technical",
            "question": f"Explain the hardest debugging issue you faced while using {secondary_skill[0]}.",
            "signal": "Practical depth",
        },
        {
            "type": "Technical",
            "question": "How do you design data validation, monitoring, and rollback for an AI feature in production?",
            "signal": "Production readiness",
        },
        {
            "type": "Technical",
            "question": f"Design an end-to-end system for {role}, including deployment, monitoring, and failure modes.",
            "signal": "Architecture maturity",
        },
    ]

    scenario_questions: List[Dict[str, str]] = [
        {
            "type": "Scenario",
            "question": f"Explain your work on {project}. What was your contribution and measurable outcome?",
            "signal": "Ownership and evidence",
        },
        {
            "type": "Scenario",
            "question": "How would you debug an AI workflow whose offline metrics look good but user outcomes are poor?",
            "signal": "Evaluation and debugging judgment",
        },
        {
            "type": "Scenario",
            "question": "A stakeholder asks for a model launch before validation is complete. How would you handle the tradeoff?",
            "signal": "Judgment under delivery pressure",
        },
    ]

    hr_questions: List[Dict[str, str]] = [
        {
            "type": "HR",
            "question": "Tell us about a time you aligned product, data, and engineering teams around an AI deliverable.",
            "signal": "Delivery and communication",
        },
        {
            "type": "HR",
            "question": "What kind of team environment helps you do your best technical work?",
            "signal": "Team fit",
        },
        {
            "type": "HR",
            "question": "Describe a time you received difficult feedback and changed your approach.",
            "signal": "Coachability",
        },
    ]

    follow_up_questions: List[Dict[str, str]] = []
    for skill in missing[:4]:
        follow_up_questions.append(
            {
                "type": "Follow-up",
                "question": f"The JD requires {skill}. What adjacent experience do you have, and how would you ramp up in 30 days?",
                "signal": "Coachability and transferability",
            }
        )

    depth_questions: List[Dict[str, str]] = []
    for skill in matched[:3]:
        depth_questions.append(
            {
                "type": "Depth Check",
                "question": f"You listed {skill}. Describe the hardest bug or tradeoff you faced while using it.",
                "signal": "Evidence beyond keyword matching",
            }
        )

    questions = technical_questions + scenario_questions + hr_questions + follow_up_questions + depth_questions
    overall = candidate.get("overall_score", scores.get("overall", 0))
    return {
        "candidate": candidate.get("name", "Unknown"),
        "recommended_round": _round_type(overall),
        "focus_areas": focus_areas,
        "questions": questions[: max(3, num_questions)],
        "question_groups": {
            "technical": technical_questions[:5],
            "scenario": scenario_questions[:3],
            "hr": hr_questions[:3],
            "follow_up": follow_up_questions,
            "depth_check": depth_questions,
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
