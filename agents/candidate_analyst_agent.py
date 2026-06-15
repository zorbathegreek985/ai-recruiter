"""
Candidate Analyst Agent.

Extracts candidate skills, experience, projects, and certifications while
preserving the existing parsed resume fields.
"""
import re
from typing import Any, Dict, List

from parsers.resume_parser import extract_structured_resume


CERTIFICATION_PATTERNS = [
    r"\bAWS Certified[^,\n;]*",
    r"\bGoogle Cloud Certified[^,\n;]*",
    r"\bMicrosoft Certified[^,\n;]*",
    r"\bCertified Kubernetes Administrator\b",
    r"\bCKA\b",
    r"\bCKAD\b",
    r"\bPMP\b",
    r"\bTensorFlow Developer Certificate\b",
    r"\bDatabricks Certified[^,\n;]*",
    r"\bAzure[^,\n;]*Certification\b",
]


def extract_certifications(text: str) -> List[str]:
    """Extract certifications from raw resume text using conservative patterns."""
    found = set()
    for pattern in CERTIFICATION_PATTERNS:
        for match in re.findall(pattern, text or "", flags=re.IGNORECASE):
            cleaned = re.sub(r"\s+", " ", match).strip(" -|.,;")
            if cleaned:
                found.add(cleaned)

    section = re.search(
        r"(?:CERTIFICATIONS?|LICENSES?)\s*[:\n](.*?)(?:\n\s*(?:SKILLS|PROJECTS|EXPERIENCE|EDUCATION)|$)",
        text or "",
        flags=re.IGNORECASE | re.DOTALL,
    )
    if section:
        bullets = re.findall(r"(?:[-*\u2022]|\n)\s*([^\n]+)", section.group(1))
        for bullet in bullets:
            cleaned = re.sub(r"\s+", " ", bullet).strip(" -|.,;")
            if 3 < len(cleaned) < 90:
                found.add(cleaned)

    return sorted(found)[:8]


def analyze_candidate(candidate_input: Any) -> Dict[str, Any]:
    """Return a structured candidate analysis with existing candidate fields intact."""
    candidate = candidate_input if isinstance(candidate_input, dict) else extract_structured_resume(candidate_input)
    text = candidate.get("raw_text", "")
    certifications = candidate.get("certifications") or extract_certifications(text)

    analysis = {
        "skills": candidate.get("skills", []),
        "experience_years": candidate.get("experience_years", 0),
        "projects": candidate.get("projects", []),
        "certifications": certifications,
    }

    return {**candidate, "certifications": certifications, "candidate_analysis": analysis}
