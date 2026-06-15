"""
Multi-agent recruiting pipeline.

Each agent keeps a narrow responsibility and returns plain dictionaries so the
existing Streamlit app can keep using the same candidate and JD data shapes.
"""
from agents.jd_analyst_agent import analyze_jd
from agents.candidate_analyst_agent import analyze_candidate
from agents.bias_agent import analyze_bias_signals
from agents.github_agent import analyze_github_profile
from agents.match_agent import analyze_match
from agents.risk_agent import analyze_candidate_risk, analyze_batch_risk
from agents.hiring_agent import generate_hiring_recommendation
from agents.interview_agent import generate_interview_plan
from agents.orchestrator import run_recruiting_pipeline, rank_candidates_with_agents

__all__ = [
    "analyze_jd",
    "analyze_candidate",
    "analyze_bias_signals",
    "analyze_github_profile",
    "analyze_match",
    "analyze_candidate_risk",
    "analyze_batch_risk",
    "generate_hiring_recommendation",
    "generate_interview_plan",
    "run_recruiting_pipeline",
    "rank_candidates_with_agents",
]
