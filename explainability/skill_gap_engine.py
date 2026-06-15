"""Advanced skill gap analysis with severity and learning recommendations."""
from typing import Any, Dict, List


CRITICAL_SKILLS = {
    "python",
    "machine learning",
    "tensorflow",
    "pytorch",
    "aws",
    "sql",
    "nlp",
    "llm",
    "docker",
    "kubernetes",
}

LEARNING_RESOURCES = {
    "python": "Build a small production API or data pipeline in Python.",
    "machine learning": "Review supervised learning, evaluation metrics, and validation.",
    "tensorflow": "Implement and deploy a compact TensorFlow model.",
    "pytorch": "Reproduce a PyTorch training loop and explain each stage.",
    "aws": "Practice S3, Lambda, EC2, and one ML deployment workflow.",
    "sql": "Solve joins, aggregations, window functions, and query optimization tasks.",
    "nlp": "Build a text classification or retrieval pipeline with evaluation.",
    "llm": "Build a small RAG workflow with citations and hallucination checks.",
    "docker": "Containerize a model-serving API and document the deployment path.",
    "kubernetes": "Understand pods, services, deployments, scaling, and logs.",
}


def _build_learning_path(priority_gaps: List[Dict[str, Any]], max_weeks: int = 4) -> List[Dict[str, str]]:
    """Create a simple week-by-week learning plan from the highest priority gaps."""
    severity_order = {"High": 0, "Medium": 1, "Low": 2}
    ordered = sorted(priority_gaps, key=lambda gap: severity_order.get(gap.get("severity", "Low"), 2))
    plan = []
    for index, gap in enumerate(ordered[:max_weeks], 1):
        skill = gap["skill"]
        plan.append(
            {
                "week": f"Week {index}",
                "skill": skill,
                "goal": gap["recommendation"],
                "deliverable": f"Create a small proof-of-skill artifact for {skill}.",
            }
        )
    return plan


def build_advanced_skill_gap(candidate: Dict[str, Any], jd: Dict[str, Any]) -> Dict[str, Any]:
    """Return prioritized skill gaps without changing the legacy gap output."""
    candidate_skills = {skill.lower(): skill for skill in candidate.get("skills", [])}
    required = jd.get("required_skills", [])
    preferred = jd.get("preferred_skills", [])

    matched_required = [skill for skill in required if skill.lower() in candidate_skills]
    missing_required = [skill for skill in required if skill.lower() not in candidate_skills]
    matched_preferred = [skill for skill in preferred if skill.lower() in candidate_skills]
    missing_preferred = [skill for skill in preferred if skill.lower() not in candidate_skills]

    priority_gaps: List[Dict[str, Any]] = []
    for skill in missing_required:
        key = skill.lower()
        severity = "High" if key in CRITICAL_SKILLS else "Medium"
        priority_gaps.append(
            {
                "skill": skill,
                "requirement": "Required",
                "severity": severity,
                "recommendation": LEARNING_RESOURCES.get(
                    key,
                    f"Validate adjacent experience and create a ramp-up plan for {skill}.",
                ),
            }
        )

    for skill in missing_preferred:
        key = skill.lower()
        priority_gaps.append(
            {
                "skill": skill,
                "requirement": "Preferred",
                "severity": "Low",
                "recommendation": LEARNING_RESOURCES.get(
                    key,
                    f"Consider this as a bonus upskilling area: {skill}.",
                ),
            }
        )

    coverage = round((len(matched_required) / max(1, len(required))) * 100, 1)
    readiness = "Ready" if coverage >= 80 else "Trainable" if coverage >= 55 else "Needs Review"

    learning_path = _build_learning_path(priority_gaps)

    return {
        "matched_required": matched_required,
        "missing_required": missing_required,
        "matched_preferred": matched_preferred,
        "missing_preferred": missing_preferred,
        "matched_skills": matched_required + matched_preferred,
        "missing_skills": missing_required + missing_preferred,
        "priority_gaps": priority_gaps,
        "recommended_learning_path": learning_path,
        "coverage": coverage,
        "readiness": readiness,
        "summary": f"{coverage}% required-skill coverage; {readiness.lower()} for recruiter follow-up.",
    }
