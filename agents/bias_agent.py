"""Bias-aware screening agent."""
import re
from typing import Any, Dict, List


PROTECTED_OR_PROXY_PATTERNS = {
    "age_proxy": [r"\b\d{2}\s*years old\b", r"\bdate of birth\b", r"\bdob\b"],
    "gender_proxy": [r"\bhe/him\b", r"\bshe/her\b", r"\bmale\b", r"\bfemale\b"],
    "marital_status": [r"\bmarried\b", r"\bsingle\b"],
    "religion_or_caste": [r"\breligion\b", r"\bcaste\b"],
    "location_proxy": [r"\bcurrent location\b", r"\bnative place\b"],
}


def analyze_bias_signals(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Flag protected/proxy signals and provide an anonymized candidate view."""
    text = candidate.get("raw_text", "") or ""
    signals: List[Dict[str, str]] = []
    lowered = text.lower()

    for category, patterns in PROTECTED_OR_PROXY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, lowered, flags=re.IGNORECASE):
                signals.append(
                    {
                        "category": category,
                        "signal": pattern.replace(r"\b", "").replace("\\", ""),
                        "guidance": "Do not use this signal for ranking or interview decisions.",
                    }
                )

    anonymized = {
        "name": "Candidate",
        "email": None,
        "phone": None,
        "skills": candidate.get("skills", []),
        "experience_years": candidate.get("experience_years", 0),
        "projects": candidate.get("projects", []),
        "education": "Education hidden in bias-aware mode",
        "scores": candidate.get("scores", {}),
        "overall_score": candidate.get("overall_score", 0),
        "rank": candidate.get("rank"),
    }

    return {
        "bias_risk_level": "Medium" if signals else "Low",
        "signals": signals,
        "anonymized_profile": anonymized,
        "fair_screening_guidance": [
            "Review skills, project evidence, experience relevance, and interview performance.",
            "Avoid using name, age, gender, marital status, caste, religion, or location as decision factors.",
            "Use education prestige only when it is explicitly job-relevant and consistently applied.",
        ],
    }
