"""
Explainable AI Layer
Uses Gemini to generate recruiter-friendly explanations for rankings.
"""
import os
from typing import Dict, List, Any, Optional
import json
import warnings

try:
    import google.generativeai as genai
except ImportError:
    genai = None

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY and genai is not None:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        GEMINI_AVAILABLE = True
    except Exception as e:
        warnings.warn(f"Gemini init failed for explanations: {e}", RuntimeWarning)
        GEMINI_AVAILABLE = False
else:
    GEMINI_AVAILABLE = False

def generate_explanation(
    candidate: Dict[str, Any],
    jd: Dict[str, Any],
    scores: Dict[str, float],
    rank: int
) -> str:
    """Generate natural language explanation using Gemini or template fallback."""
    
    if not GEMINI_AVAILABLE:
        return _template_explanation(candidate, jd, scores, rank)
    
    prompt = f"""
You are an expert AI recruiter. Provide a concise, professional, recruiter-style explanation (2-4 sentences) for why this candidate ranked #{rank}.

**Job Description Summary:**
- Role: {jd.get('role_category', 'ML Role')}
- Required Skills: {', '.join(jd.get('required_skills', []))}
- Experience: {jd.get('experience', 'Not specified')}
- Education: {jd.get('education', 'Not specified')}

**Candidate:**
- Name: {candidate.get('name', 'Unknown')}
- Skills: {', '.join(candidate.get('skills', [])[:8])}
- Experience: {candidate.get('experience_years', 0)} years
- Projects: {', '.join(candidate.get('projects', [])[:3])}
- Education: {candidate.get('education', 'N/A')[:80]}

**Scores (0-100):**
- Overall: {scores.get('overall', 0)}
- Skill Match: {scores.get('skill_match', 0)}
- Experience: {scores.get('experience', 0)}
- Projects: {scores.get('projects', 0)}
- Education: {scores.get('education', 0)}

Focus on:
1. Key matching strengths (skills, experience, projects)
2. Any notable gaps
3. Why the overall score makes sense for this rank
4. Use specific numbers from scores where helpful

Keep it objective, positive where deserved, and actionable. Do not mention the model or scores formula.
"""

    try:
        response = model.generate_content(prompt)
        explanation = response.text.strip()
        if len(explanation) > 20:
            return explanation
    except Exception as e:
        warnings.warn(f"Gemini explanation error: {e}", RuntimeWarning)
    
    return _template_explanation(candidate, jd, scores, rank)

def _template_explanation(candidate: Dict[str, Any], jd: Dict[str, Any], scores: Dict[str, float], rank: int) -> str:
    """Fallback template-based explanation."""
    name = candidate.get("name", "The candidate")
    overall = scores.get("overall", 0)
    skill = scores.get("skill_match", 0)
    exp = scores.get("experience", 0)
    
    strengths = []
    if skill > 80:
        strengths.append(f"strong skill alignment ({skill}%)")
    if exp > 80:
        strengths.append(f"sufficient experience ({candidate.get('experience_years', 0)} years)")
    
    gaps = []
    jd_req = set(s.lower() for s in jd.get("required_skills", []))
    cand_sk = set(s.lower() for s in candidate.get("skills", []))
    missing = jd_req - cand_sk
    if missing:
        gaps.append(f"missing some skills like {list(missing)[:2]}")
    
    base = f"{name} ranks #{rank} with an overall match of {overall}%. "
    if strengths:
        base += f"Key strengths include {', '.join(strengths)}. "
    if gaps:
        base += f"Potential gaps: {', '.join(gaps)}. "
    else:
        base += "Excellent fit across most dimensions. "
    
    base += "Strong semantic alignment with the job requirements."
    return base

def generate_skill_gap_analysis(
    candidate: Dict[str, Any],
    jd: Dict[str, Any]
) -> Dict[str, Any]:
    """Detailed skill gap analysis."""
    cand_skills = [s.lower() for s in candidate.get("skills", [])]
    req = [s for s in jd.get("required_skills", [])]
    pref = [s for s in jd.get("preferred_skills", [])]
    
    matched = []
    missing = []
    
    for skill in req:
        if skill.lower() in cand_skills:
            matched.append(skill)
        else:
            missing.append(skill)
    
    pref_matched = [s for s in pref if s.lower() in cand_skills]
    pref_missing = [s for s in pref if s.lower() not in cand_skills]
    
    total_req = len(req) if req else 1
    match_pct = round((len(matched) / total_req) * 100, 1)
    
    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "preferred_matched": pref_matched,
        "preferred_missing": pref_missing,
        "match_percentage": match_pct,
        "total_required": len(req),
        "total_matched": len(matched)
    }

def generate_interview_questions(
    candidate: Dict[str, Any],
    jd: Dict[str, Any],
    num_questions: int = 5
) -> List[str]:
    """Bonus: Generate tailored interview questions using Gemini or template."""
    if not GEMINI_AVAILABLE:
        return _template_questions(candidate, jd, num_questions)
    
    prompt = f"""
Generate {num_questions} insightful, role-specific interview questions for this candidate applying to the ML Engineer position.

Candidate strengths: {', '.join(candidate.get('skills', [])[:6])}
Candidate projects: {', '.join(candidate.get('projects', [])[:2])}
JD required skills: {', '.join(jd.get('required_skills', []))}

Mix of:
- Technical deep dives
- Experience-based
- Problem solving / system design
- Behavioral

Return only the numbered list of questions, one per line.
"""
    try:
        response = model.generate_content(prompt)
        questions = [q.strip() for q in response.text.strip().split('\n') if q.strip() and q.strip()[0].isdigit() or q.strip().startswith('-')]
        return questions[:num_questions] or _template_questions(candidate, jd, num_questions)
    except:
        return _template_questions(candidate, jd, num_questions)

def _template_questions(candidate: Dict[str, Any], jd: Dict[str, Any], num: int) -> List[str]:
    """Fallback questions."""
    base = [
        f"Walk us through your experience with {jd.get('required_skills', ['Python'])[0]}.",
        "Describe a challenging ML project you led end-to-end.",
        "How do you approach model deployment and monitoring in production?",
        "Tell us about a time you had to deal with messy or incomplete data.",
        "What recent advancements in LLMs or MLOps excite you the most?"
    ]
    return base[:num]

if __name__ == "__main__":
    cand = {"name": "John Doe", "skills": ["Python", "TensorFlow", "AWS"], "experience_years": 4, "projects": ["RAG system"]}
    jd = {"required_skills": ["Python", "TensorFlow", "AWS", "NLP"], "role_category": "ML Engineer"}
    scores = {"overall": 91.25, "skill_match": 95, "experience": 90, "projects": 85, "education": 80}
    
    print(generate_explanation(cand, jd, scores, 1))
    print("\n--- Skill Gap ---")
    print(generate_skill_gap_analysis(cand, jd))
