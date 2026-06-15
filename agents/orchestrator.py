"""
Recruiting pipeline orchestrator.

Runs the JD, candidate, match, risk, and hiring agents together while preserving
the ranked candidate structure expected by the original Streamlit app.
"""
from typing import Any, Dict, List, Optional

from agents.candidate_analyst_agent import analyze_candidate
from agents.hiring_agent import generate_hiring_recommendation
from agents.jd_analyst_agent import analyze_jd
from agents.match_agent import analyze_match
from agents.risk_agent import analyze_batch_risk, analyze_candidate_risk


def run_recruiting_pipeline(candidates: List[Dict[str, Any]], jd: Dict[str, Any]) -> Dict[str, Any]:
    """Run all agents and return analyzed JD plus ranked candidates."""
    analyzed_jd = analyze_jd(jd)
    analyzed_candidates = [analyze_candidate(candidate) for candidate in candidates]
    batch_risk = analyze_batch_risk(analyzed_candidates)

    enriched = []
    for candidate in analyzed_candidates:
        match = analyze_match(candidate, analyzed_jd)
        risk = analyze_candidate_risk(candidate, batch_risk)
        hiring = generate_hiring_recommendation(candidate, analyzed_jd, match, risk)
        scores = match["scores"]

        enriched.append(
            {
                **candidate,
                "scores": scores,
                "overall_score": scores["overall"],
                "agent_analysis": {
                    "jd": analyzed_jd.get("jd_analysis", {}),
                    "candidate": candidate.get("candidate_analysis", {}),
                    "match": {
                        "semantic_fit": match["semantic_fit"],
                        "skill_match": match["skill_match"],
                        "experience_match": match["experience_match"],
                    },
                },
                "risk_report": risk,
                "hiring_recommendation": hiring,
            }
        )

    ranked = sorted(enriched, key=lambda item: item["overall_score"], reverse=True)
    for rank, candidate in enumerate(ranked, 1):
        candidate["rank"] = rank

    return {"jd": analyzed_jd, "candidates": ranked, "batch_risk": batch_risk}


def rank_candidates_with_agents(
    candidates: List[Dict[str, Any]],
    jd: Dict[str, Any],
    top_k: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Compatibility wrapper for the previous rank_candidates API."""
    ranked = run_recruiting_pipeline(candidates, jd)["candidates"]
    return ranked[:top_k] if top_k else ranked
