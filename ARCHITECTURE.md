# AI Recruiter Architecture

## System Overview

```text
Recruiter / Judge
      |
      v
Streamlit App (app.py)
      |
      +-- Job Description Intake
      |     +-- agents.jd_analyst_agent
      |     +-- parsers.jd_parser
      |
      +-- Resume Intake
      |     +-- agents.candidate_analyst_agent
      |     +-- parsers.resume_parser
      |
      +-- Multi-Agent Orchestration
      |     +-- match_agent
      |     +-- risk_agent
      |     +-- hiring_agent
      |     +-- interview_agent
      |     +-- bias_agent
      |     +-- github_agent
      |
      +-- Scoring and Explainability
      |     +-- ranking.ranking_engine
      |     +-- explainability.explanation_engine
      |     +-- explainability.scoring_explainer
      |     +-- explainability.skill_gap_engine
      |
      +-- Search and Analytics
      |     +-- embeddings.embedding_engine
      |     +-- rag.faiss_search
      |     +-- dashboard.analytics
      |     +-- dashboard.recruiter_dashboard
      |
      +-- Recruiter Outputs
            +-- reports.pdf_report
            +-- shortlist CSV
            +-- interview kits
            +-- bias-aware profile
```

## Feature Architecture

1. AI Interview Agent
   - Module: `agents/interview_agent.py`
   - Input: candidate, JD, skill gaps
   - Output: focus areas, interview questions, scorecard, red flags

2. Skill Gap Analysis
   - Module: `explainability/skill_gap_engine.py`
   - Input: candidate skills and JD requirements
   - Output: required/preferred gaps, severity, readiness, recommendations

3. Recruiter Dashboard
   - Module: `dashboard/recruiter_dashboard.py`
   - Input: ranked candidates
   - Output: decision table, shortlist CSV, batch KPIs

4. Batch Resume Analysis
   - Module: `dashboard/recruiter_dashboard.py`
   - Input: all ranked candidates
   - Output: aggregate hiring recommendations, risk level, recurring gaps

5. Explainable Scoring
   - Module: `explainability/scoring_explainer.py`
   - Input: candidate, JD, score breakdown
   - Output: dimension evidence and weighted contribution

6. Candidate PDF Reports
   - Module: `reports/pdf_report.py`
   - Input: candidate, JD, score evidence, gaps, interview plan
   - Output: downloadable PDF report

7. Bias-Aware Screening
   - Module: `agents/bias_agent.py`
   - Input: parsed candidate profile
   - Output: protected/proxy signal warnings and anonymized profile

8. GitHub Profile Analyzer
   - Module: `agents/github_agent.py`
   - Input: resume raw text
   - Output: optional public repository signals when a GitHub URL is present

9. Multi-Agent Orchestration
   - Module: `agents/orchestrator.py`
   - Input: parsed resumes and analyzed JD
   - Output: backward-compatible ranked candidates with enriched agent reports

## Backward Compatibility

Existing consumers can continue reading:

- `scores`
- `overall_score`
- `rank`
- `agent_analysis`
- `risk_report`
- `hiring_recommendation`

New features add fields rather than replacing existing fields:

- `advanced_skill_gap`
- `score_evidence`
- `interview_plan`
- `bias_report`
- `github_report`
