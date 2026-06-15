# Agents Architecture

The `agents` package adds a modular multi-agent layer without changing the
existing parser, ranking, RAG, analytics, or Streamlit data contracts.

- `jd_analyst_agent.py`: extracts required skills, preferred skills, experience requirements, and industry/domain.
- `candidate_analyst_agent.py`: extracts candidate skills, experience, projects, and certifications.
- `match_agent.py`: calculates semantic fit, skill match, and experience match.
- `risk_agent.py`: detects keyword stuffing, resume anomalies, and duplicate resumes.
- `hiring_agent.py`: generates recommendation, confidence score, strengths, weaknesses, and missing skills.
- `interview_agent.py`: creates structured technical, project, system design, and gap-validation interview kits.
- `bias_agent.py`: flags protected/proxy signals and returns anonymized screening profiles.
- `github_agent.py`: detects GitHub profiles and optionally analyzes public repository signals.
- `orchestrator.py`: runs the agents together and returns ranked candidates with the same fields the app already expects.

Primary entry point:

```python
from agents import rank_candidates_with_agents
```

The returned candidates still include `scores`, `overall_score`, and `rank`,
with additional `agent_analysis`, `risk_report`, `hiring_recommendation`,
`advanced_skill_gap`, `score_evidence`, `interview_plan`, `bias_report`, and
`github_report` fields for richer UI, reporting, and downstream workflows.
