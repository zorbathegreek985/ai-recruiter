"""
Multi-agent recruiting pipeline.

Each agent keeps a narrow responsibility and returns plain dictionaries so the
existing Streamlit app can keep using the same candidate and JD data shapes.
"""
from agents.jd_analyst_agent import analyze_jd
from agents.candidate_analyst_agent import analyze_candidate
from agents.match_agent import analyze_match
from agents.risk_agent import analyze_candidate_risk, analyze_batch_risk
from agents.hiring_agent import generate_hiring_recommendation
from agents.orchestrator import run_recruiting_pipeline, rank_candidates_with_agents

__all__ = [
    "analyze_jd",
    "analyze_candidate",
    "analyze_match",
    "analyze_candidate_risk",
    "analyze_batch_risk",
    "generate_hiring_recommendation",
    "run_recruiting_pipeline",
    "rank_candidates_with_agents",
]
