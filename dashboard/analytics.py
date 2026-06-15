from __future__ import annotations

"""
Analytics Dashboard Module
Provides visualizations and aggregate stats using Plotly.
"""
import pandas as pd
from typing import List, Dict, Any
import numpy as np

try:
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    px = None
    go = None


def _empty_figure():
    return go.Figure() if go is not None else None

def create_ranking_distribution_chart(ranked_candidates: List[Dict[str, Any]]) -> go.Figure:
    """Bar chart of overall scores by rank."""
    if not ranked_candidates or px is None:
        return _empty_figure()
    
    df = pd.DataFrame([{
        "Rank": c["rank"],
        "Name": c.get("name", "Unknown")[:20],
        "Overall Score": c.get("overall_score", 0),
        "Skill Match": c.get("scores", {}).get("skill_match", 0),
    } for c in ranked_candidates])
    
    fig = px.bar(
        df,
        x="Name",
        y="Overall Score",
        color="Skill Match",
        title="Candidate Ranking Distribution",
        labels={"Overall Score": "Overall Match %"},
        color_continuous_scale="Viridis",
        hover_data=["Rank"]
    )
    fig.update_layout(xaxis_tickangle=-45, height=400)
    return fig

def create_score_breakdown_chart(candidate: Dict[str, Any]) -> go.Figure:
    """Radar / bar for one candidate's score components."""
    if "scores" not in candidate or go is None:
        return _empty_figure()
    
    scores = candidate["scores"]
    categories = ["Skill Match", "Experience", "Projects", "Education"]
    values = [scores.get("skill_match", 0), scores.get("experience", 0), 
              scores.get("projects", 0), scores.get("education", 0)]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        name=candidate.get("name", "")
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        title=f"Score Breakdown: {candidate.get('name', 'Candidate')}"
    )
    return fig

def create_top_skills_chart(all_candidates: List[Dict[str, Any]], top_n: int = 10) -> go.Figure:
    """Horizontal bar of most common skills across candidates."""
    skill_counts = {}
    for cand in all_candidates:
        for skill in cand.get("skills", []):
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
    
    if not skill_counts or px is None:
        return _empty_figure()
    
    sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    df = pd.DataFrame(sorted_skills, columns=["Skill", "Count"])
    
    fig = px.bar(
        df,
        x="Count",
        y="Skill",
        orientation="h",
        title=f"Top {top_n} Skills Across Candidates",
        color="Count",
        color_continuous_scale="Blues"
    )
    fig.update_layout(height=350, yaxis={'categoryorder': 'total ascending'})
    return fig

def create_skill_gap_frequency_chart(ranked_candidates: List[Dict[str, Any]], jd: Dict[str, Any]) -> go.Figure:
    """Bar chart showing frequency of missing skills."""
    from explainability.explanation_engine import generate_skill_gap_analysis
    
    missing_counts = {}
    for cand in ranked_candidates:
        gaps = generate_skill_gap_analysis(cand, jd)
        for skill in gaps.get("missing_skills", []):
            missing_counts[skill] = missing_counts.get(skill, 0) + 1
    
    if not missing_counts or px is None:
        return _empty_figure()
    
    df = pd.DataFrame(list(missing_counts.items()), columns=["Missing Skill", "Frequency"])
    df = df.sort_values("Frequency", ascending=False)
    
    fig = px.bar(
        df,
        x="Missing Skill",
        y="Frequency",
        title="Skill Gap Frequency (How often missing across candidates)",
        color="Frequency",
        color_continuous_scale="Reds"
    )
    fig.update_layout(height=350, xaxis_tickangle=-30)
    return fig

def create_average_match_gauge(ranked_candidates: List[Dict[str, Any]]) -> go.Figure:
    """Simple gauge / indicator for average match score."""
    if go is None:
        return _empty_figure()
    if not ranked_candidates:
        avg = 50
    else:
        avg = np.mean([c.get("overall_score", 0) for c in ranked_candidates])
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=avg,
        title={"text": "Average Match Score"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "darkblue"},
            "steps": [
                {"range": [0, 50], "color": "lightgray"},
                {"range": [50, 75], "color": "yellow"},
                {"range": [75, 100], "color": "lightgreen"}
            ],
            "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": 90}
        }
    ))
    fig.update_layout(height=250)
    return fig

def get_summary_stats(ranked_candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute key metrics for dashboard."""
    if not ranked_candidates:
        return {"total": 0, "avg_score": 0, "top_score": 0, "high_match": 0}
    
    scores = [c.get("overall_score", 0) for c in ranked_candidates]
    return {
        "total": len(ranked_candidates),
        "avg_score": round(np.mean(scores), 1),
        "top_score": round(max(scores), 1),
        "high_match": sum(1 for s in scores if s >= 80),
        "medium_match": sum(1 for s in scores if 60 <= s < 80),
        "low_match": sum(1 for s in scores if s < 60)
    }

if __name__ == "__main__":
    # Test data
    test_cands = [
        {"name": "John", "rank": 1, "overall_score": 91, "scores": {"skill_match": 95, "experience": 90, "projects": 85, "education": 80}, "skills": ["Python", "TensorFlow", "AWS"]},
        {"name": "Alice", "rank": 2, "overall_score": 82, "scores": {"skill_match": 88, "experience": 75, "projects": 90, "education": 85}, "skills": ["Python", "PyTorch", "NLP"]},
    ]
    jd = {"required_skills": ["Python", "TensorFlow", "AWS"]}
    
    print("Stats:", get_summary_stats(test_cands))
    print("Distribution chart created (object)")
