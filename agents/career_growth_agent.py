"""Career Growth Agent for candidate upskilling roadmaps."""
from typing import Any, Dict, List

from explainability.skill_gap_engine import build_advanced_skill_gap


def _priority_label(gap: Dict[str, Any]) -> str:
    severity = gap.get("severity", "Low")
    requirement = gap.get("requirement", "Preferred")
    if severity == "High" or requirement == "Required":
        return "High"
    if severity == "Medium":
        return "Medium"
    return "Low"


def generate_growth_plan(candidate: Dict[str, Any], jd: Dict[str, Any]) -> Dict[str, Any]:
    """Build a four-week growth roadmap and projected match score."""
    gap_report = candidate.get("advanced_skill_gap") or build_advanced_skill_gap(candidate, jd)
    priority_gaps = gap_report.get("priority_gaps", [])
    current_score = candidate.get("overall_score", candidate.get("scores", {}).get("overall", 0))

    roadmap: List[Dict[str, Any]] = []
    if priority_gaps:
        for index, gap in enumerate(priority_gaps[:4], 1):
            roadmap.append(
                {
                    "week": f"Week {index}",
                    "focus": gap.get("skill", "Role readiness"),
                    "priority": _priority_label(gap),
                    "goal": gap.get("recommendation", "Build a practical proof-of-skill artifact."),
                    "deliverable": f"Create evidence that demonstrates {gap.get('skill', 'the gap')} in a job-relevant workflow.",
                }
            )

    while len(roadmap) < 4:
        week = len(roadmap) + 1
        roadmap.append(
            {
                "week": f"Week {week}",
                "focus": "Interview readiness" if week == 4 else "Project evidence",
                "priority": "Medium",
                "goal": "Convert existing experience into recruiter-verifiable examples.",
                "deliverable": "Prepare a concise project walkthrough with metrics, tradeoffs, and lessons learned.",
            }
        )

    high_priority = sum(1 for gap in priority_gaps if _priority_label(gap) == "High")
    medium_priority = sum(1 for gap in priority_gaps if _priority_label(gap) == "Medium")
    projected_gain = min(18, high_priority * 5 + medium_priority * 3 + max(0, 4 - len(priority_gaps)) * 1.5)
    projected_score = min(100, round(current_score + projected_gain, 1))

    return {
        "candidate": candidate.get("name", "Unknown"),
        "current_match_score": round(current_score, 1),
        "projected_match_score": projected_score,
        "missing_skills": gap_report.get("missing_skills", []),
        "skill_priority": [
            {
                "skill": gap.get("skill"),
                "priority": _priority_label(gap),
                "requirement": gap.get("requirement", "Required"),
            }
            for gap in priority_gaps
        ],
        "roadmap": roadmap[:4],
        "summary": (
            f"{candidate.get('name', 'Candidate')} can plausibly improve from "
            f"{round(current_score, 1)}% to {projected_score}% by closing the highest-priority gaps."
        ),
    }
