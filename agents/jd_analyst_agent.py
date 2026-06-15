"""
JD Analyst Agent.

Extracts job description requirements and domain context. It builds on the
existing parser to avoid changing the behavior users already rely on.
"""
import re
from typing import Any, Dict, List

from parsers.jd_parser import extract_structured_jd


DOMAIN_KEYWORDS = {
    "Healthcare": ["healthcare", "clinical", "patient", "medical", "hospital", "biotech"],
    "Finance": ["finance", "banking", "trading", "risk", "fraud", "payment", "fintech"],
    "E-commerce": ["e-commerce", "ecommerce", "retail", "marketplace", "recommendation"],
    "SaaS": ["saas", "subscription", "crm", "b2b", "enterprise software"],
    "AI/ML": ["machine learning", "deep learning", "nlp", "llm", "computer vision", "mlops"],
    "Cloud/Platform": ["cloud", "aws", "azure", "gcp", "kubernetes", "platform"],
}


def _infer_domain(text: str, role_category: str = "") -> str:
    haystack = f"{role_category}\n{text}".lower()
    matches = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in haystack)
        if score:
            matches.append((score, domain))

    if not matches:
        return "General Technology"

    matches.sort(reverse=True)
    return matches[0][1]


def _extract_experience_years(experience_text: str) -> Dict[str, Any]:
    numbers = [int(n) for n in re.findall(r"\d+", experience_text or "")]
    if not numbers:
        return {"minimum_years": None, "maximum_years": None, "raw": experience_text or "Not specified"}

    minimum = min(numbers)
    maximum = max(numbers) if len(numbers) > 1 else None
    if "+" in experience_text:
        maximum = None

    return {"minimum_years": minimum, "maximum_years": maximum, "raw": experience_text}


def analyze_jd(jd_input: Any) -> Dict[str, Any]:
    """Return a structured JD analysis with required fields for downstream agents."""
    jd = jd_input if isinstance(jd_input, dict) else extract_structured_jd(jd_input)
    text = jd.get("raw_text", "")
    experience_requirements = _extract_experience_years(jd.get("experience", ""))
    industry_domain = _infer_domain(text, jd.get("role_category", ""))

    profile = {
        "role_category": jd.get("role_category", "General Role"),
        "industry_domain": industry_domain,
        "required_skills": jd.get("required_skills", []),
        "preferred_skills": jd.get("preferred_skills", []),
        "experience_requirements": experience_requirements,
        "education_requirements": jd.get("education", "Not specified"),
        "raw_text_preview": (text or "")[:500],
    }

    analysis = {
        "profile": profile,
        "required_skills": jd.get("required_skills", []),
        "preferred_skills": jd.get("preferred_skills", []),
        "experience_requirements": experience_requirements,
        "education_requirements": jd.get("education", "Not specified"),
        "industry_domain": industry_domain,
    }

    return {
        **jd,
        "jd_profile": profile,
        "jd_analysis": analysis,
        "industry_domain": analysis["industry_domain"],
    }


def summarize_jd_requirements(jd: Dict[str, Any]) -> Dict[str, List[str]]:
    """Small helper for UIs or tests that only need skill buckets."""
    analyzed = analyze_jd(jd)
    return {
        "required_skills": analyzed["jd_analysis"]["required_skills"],
        "preferred_skills": analyzed["jd_analysis"]["preferred_skills"],
    }
