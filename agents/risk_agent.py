"""
Risk Agent.

Detects keyword stuffing, resume anomalies, and possible duplicates. These are
review signals, not final hiring decisions.
"""
import hashlib
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _fingerprint(candidate: Dict[str, Any]) -> str:
    text = _normalize_text(candidate.get("raw_text", ""))
    if not text:
        text = _normalize_text(
            " ".join(
                [
                    candidate.get("name", ""),
                    candidate.get("email", "") or "",
                    " ".join(candidate.get("skills", [])),
                    " ".join(candidate.get("projects", [])),
                ]
            )
        )
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def detect_keyword_stuffing(candidate: Dict[str, Any]) -> Dict[str, Any]:
    text = _normalize_text(candidate.get("raw_text", ""))
    tokens = re.findall(r"[a-z][a-z+#.]{1,30}", text)
    total = len(tokens) or 1
    counts = Counter(tokens)
    repeated = [
        {"keyword": word, "count": count}
        for word, count in counts.most_common(8)
        if count >= 8 and count / total >= 0.025
    ]

    skill_repetitions = []
    for skill in candidate.get("skills", []):
        count = len(re.findall(r"\b" + re.escape(skill.lower()) + r"\b", text))
        if count >= 8:
            skill_repetitions.append({"keyword": skill, "count": count})

    signals = repeated + [s for s in skill_repetitions if s not in repeated]
    score = min(40, len(signals) * 15)
    return {"detected": bool(signals), "score": score, "signals": signals[:8]}


def detect_resume_anomalies(candidate: Dict[str, Any]) -> Dict[str, Any]:
    reasons = []
    text = candidate.get("raw_text", "") or ""

    if len(text) < 800:
        reasons.append("Unusually short resume content")
    if candidate.get("experience_years", 0) > 5 and len(candidate.get("skills", [])) < 4:
        reasons.append("High experience claimed with very few extracted skills")
    if candidate.get("experience_years", 0) == 0:
        reasons.append("No experience duration could be extracted")
    if not candidate.get("email"):
        reasons.append("No email address detected")
    if not candidate.get("projects") or candidate.get("projects") == ["Not specified"]:
        reasons.append("No clear project evidence detected")

    score = min(45, len(reasons) * 12)
    return {"detected": bool(reasons), "score": score, "reasons": reasons}


def analyze_batch_risk(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Detect duplicates across a batch using identity and content fingerprints."""
    seen_names = {}
    seen_emails = {}
    seen_fingerprints = {}
    duplicates: List[Tuple[str, str, str]] = []

    for candidate in candidates:
        name = (candidate.get("name") or "").strip().lower()
        email = (candidate.get("email") or "").strip().lower()
        display = candidate.get("name", "Unknown")
        fp = _fingerprint(candidate)

        if name and name in seen_names:
            duplicates.append((seen_names[name], display, "same name"))
        else:
            seen_names[name] = display

        if email and email in seen_emails:
            duplicates.append((seen_emails[email], display, "same email"))
        elif email:
            seen_emails[email] = display

        if fp in seen_fingerprints:
            duplicates.append((seen_fingerprints[fp], display, "same resume content"))
        else:
            seen_fingerprints[fp] = display

    unique = sorted(set(duplicates))
    return {
        "duplicates": [
            {"candidate_a": a, "candidate_b": b, "reason": reason}
            for a, b, reason in unique
        ]
    }


def analyze_candidate_risk(
    candidate: Dict[str, Any],
    batch_risk: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    keyword_stuffing = detect_keyword_stuffing(candidate)
    anomalies = detect_resume_anomalies(candidate)
    duplicates = []

    if batch_risk:
        name = candidate.get("name", "Unknown")
        duplicates = [
            duplicate
            for duplicate in batch_risk.get("duplicates", [])
            if duplicate["candidate_a"] == name or duplicate["candidate_b"] == name
        ]

    risk_score = keyword_stuffing["score"] + anomalies["score"] + min(30, len(duplicates) * 20)
    risk_score = min(100, risk_score)

    if risk_score >= 60:
        level = "High"
    elif risk_score >= 30:
        level = "Medium"
    else:
        level = "Low"

    return {
        "risk_score": risk_score,
        "risk_level": level,
        "keyword_stuffing": keyword_stuffing,
        "anomalies": anomalies,
        "duplicates": duplicates,
    }
