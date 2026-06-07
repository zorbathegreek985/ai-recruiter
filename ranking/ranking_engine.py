"""
Candidate Ranking Engine
Computes weighted overall score and ranks candidates.
"""
import numpy as np
from typing import List, Dict, Any, Tuple
from embeddings.embedding_engine import semantic_similarity, get_embedding, compute_cosine_similarity

# Weights as per spec
WEIGHTS = {
    "skill_match": 0.45,
    "experience": 0.30,
    "projects": 0.15,
    "education": 0.10
}

def normalize_score(score: float, min_val: float = 0, max_val: float = 100) -> float:
    """Normalize to 0-100 range."""
    return max(min_val, min(max_val, score))

def compute_skill_match_score(candidate_skills: List[str], jd_required: List[str], jd_preferred: List[str] = None) -> float:
    """Compute skill match score (0-100). Uses semantic + exact."""
    if not jd_required:
        return 50.0
    
    candidate_set = set(s.lower() for s in candidate_skills)
    required_set = set(s.lower() for s in jd_required)
    preferred_set = set(s.lower() for s in (jd_preferred or []))
    
    # Exact matches
    exact_required = len(candidate_set & required_set)
    exact_preferred = len(candidate_set & preferred_set)
    
    # Semantic boost using embeddings for unmatched
    semantic_score = 0.0
    unmatched_required = [s for s in jd_required if s.lower() not in candidate_set]
    
    if unmatched_required and candidate_skills:
        for req in unmatched_required:
            best_sim = max([semantic_similarity(req, cs) for cs in candidate_skills], default=0.0)
            semantic_score += best_sim * 100
    
    if unmatched_required:
        semantic_score /= len(unmatched_required)
    
    # Base score
    req_match = (exact_required / len(jd_required)) * 100 if jd_required else 0
    pref_bonus = (exact_preferred / max(1, len(preferred_set))) * 20 if preferred_set else 0
    
    total = req_match + pref_bonus + (semantic_score * 0.3)  # semantic contributes 30%
    return normalize_score(total, 0, 100)

def compute_experience_score(candidate_years: int, jd_exp_text: str) -> float:
    """Score experience match."""
    # Parse JD required years
    import re
    years_match = re.search(r'(\d+)', jd_exp_text)
    required_years = int(years_match.group(1)) if years_match else 2
    
    if candidate_years >= required_years:
        score = 100
    elif candidate_years >= required_years * 0.7:
        score = 75 + (candidate_years - required_years * 0.7) * 50
    else:
        score = (candidate_years / max(required_years, 1)) * 70
    
    return normalize_score(score)

def compute_projects_score(candidate_projects: List[str], jd_text: str) -> float:
    """Score projects relevance using semantic similarity."""
    if not candidate_projects:
        return 30.0
    
    # Simple: count relevant keywords + semantic
    jd_lower = jd_text.lower()
    relevant_keywords = ["nlp", "llm", "machine learning", "tensorflow", "pytorch", "aws", "recommendation", "fraud", "rag", "chatbot", "detection", "deployment"]
    
    keyword_score = 0
    for proj in candidate_projects:
        proj_lower = proj.lower()
        matches = sum(1 for kw in relevant_keywords if kw in proj_lower or kw in jd_lower and kw in proj_lower)
        keyword_score += min(matches * 20, 60)
    
    avg_keyword = keyword_score / len(candidate_projects) if candidate_projects else 0
    
    # Semantic: compare projects to JD
    semantic_scores = []
    for proj in candidate_projects[:3]:
        sim = semantic_similarity(proj, jd_text[:500])
        semantic_scores.append(sim * 100)
    
    avg_semantic = np.mean(semantic_scores) if semantic_scores else 40
    
    total = (avg_keyword * 0.6) + (avg_semantic * 0.4)
    return normalize_score(total, 20, 100)

def compute_education_score(edu_text: str, jd_edu: str) -> float:
    """Simple education match."""
    edu_lower = edu_text.lower()
    score = 60  # base
    
    if any(x in edu_lower for x in ["iit", "nit", "bits", "stanford", "mit", "berkeley", "phd", "master", "m.tech", "m.s"]):
        score += 25
    if any(x in edu_lower for x in ["b.tech", "bachelor", "b.e", "b.sc"]):
        score += 15
    
    if "computer science" in edu_lower or "data science" in edu_lower or "ai" in edu_lower or "machine learning" in edu_lower:
        score += 10
    
    return normalize_score(score, 40, 100)

def compute_overall_score(
    candidate: Dict[str, Any],
    jd: Dict[str, Any]
) -> Dict[str, float]:
    """Compute all component scores and overall."""
    skill_score = compute_skill_match_score(
        candidate.get("skills", []),
        jd.get("required_skills", []),
        jd.get("preferred_skills", [])
    )
    
    exp_score = compute_experience_score(
        candidate.get("experience_years", 0),
        jd.get("experience", "")
    )
    
    proj_score = compute_projects_score(
        candidate.get("projects", []),
        jd.get("raw_text", "")
    )
    
    edu_score = compute_education_score(
        candidate.get("education", ""),
        jd.get("education", "")
    )
    
    overall = (
        WEIGHTS["skill_match"] * skill_score +
        WEIGHTS["experience"] * exp_score +
        WEIGHTS["projects"] * proj_score +
        WEIGHTS["education"] * edu_score
    )
    
    return {
        "overall": round(overall, 2),
        "skill_match": round(skill_score, 2),
        "experience": round(exp_score, 2),
        "projects": round(proj_score, 2),
        "education": round(edu_score, 2)
    }

def rank_candidates(
    candidates: List[Dict[str, Any]],
    jd: Dict[str, Any],
    top_k: int = None
) -> List[Dict[str, Any]]:
    """Rank candidates and attach scores + rank."""
    scored = []
    for cand in candidates:
        scores = compute_overall_score(cand, jd)
        scored.append({
            **cand,
            "scores": scores,
            "overall_score": scores["overall"]
        })
    
    # Sort descending
    ranked = sorted(scored, key=lambda x: x["overall_score"], reverse=True)
    
    for rank, cand in enumerate(ranked, 1):
        cand["rank"] = rank
    
    if top_k:
        ranked = ranked[:top_k]
    
    return ranked

if __name__ == "__main__":
    # Quick test
    sample_cand = {
        "name": "John Doe",
        "skills": ["Python", "TensorFlow", "AWS", "NLP", "PyTorch"],
        "experience_years": 4,
        "projects": ["LLM Resume Screening", "Fraud Detection"],
        "education": "M.Tech IIT Delhi"
    }
    sample_jd = {
        "required_skills": ["Python", "TensorFlow", "AWS", "Machine Learning"],
        "preferred_skills": ["NLP", "Docker"],
        "experience": "3+ years",
        "education": "Bachelor's or Master's",
        "raw_text": "Senior Machine Learning Engineer role..."
    }
    
    scores = compute_overall_score(sample_cand, sample_jd)
    print("Test scores:", scores)
    
    ranked = rank_candidates([sample_cand], sample_jd)
    print("Rank:", ranked[0]["rank"])
