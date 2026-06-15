"""
Resume Parser Module
Parses PDF resumes into structured JSON using PyMuPDF, optional pdfplumber, and spaCy.
Handles various formats, extracts name, email, skills, education, experience, projects.
"""
import fitz  # PyMuPDF
import spacy
import re
import json
from typing import Dict, List, Any, Optional
import os
import warnings

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

PDFPLUMBER_MISSING_MESSAGE = (
    "pdfplumber is not installed. The app can still run and parse most PDFs with "
    "PyMuPDF, but difficult scanned or layout-heavy PDFs may extract less text."
)


def get_optional_dependency_warnings() -> List[str]:
    """Return parser dependency warnings that should be shown in the UI."""
    return [] if pdfplumber is not None else [PDFPLUMBER_MISSING_MESSAGE]

# Load spaCy model (small for speed)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = spacy.blank("en")

# Predefined Skill Ontology (expandable)
SKILL_ONTOLOGY = {
    "Programming": ["Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "SQL", "R", "Go", "Rust", "Scala"],
    "Machine Learning": ["TensorFlow", "PyTorch", "Scikit-learn", "XGBoost", "LightGBM", "Keras", "Hugging Face", "Transformers", "MLflow"],
    "NLP / LLM": ["NLP", "BERT", "GPT", "LLM", "LangChain", "LlamaIndex", "RAG", "Transformers", "spaCy", "NLTK", "OpenAI", "Gemini", "Prompt Engineering"],
    "Data Science": ["Pandas", "NumPy", "Matplotlib", "Seaborn", "SciPy", "SQL", "Spark", "Hadoop", "Airflow"],
    "Cloud": ["AWS", "SageMaker", "EC2", "S3", "Lambda", "Azure", "GCP", "Vertex AI", "Docker", "Kubernetes"],
    "MLOps / Tools": ["Docker", "Kubernetes", "FastAPI", "Flask", "Git", "CI/CD", "Jenkins", "MLflow", "Kubeflow"],
    "Other": ["Computer Vision", "Recommendation Systems", "Fraud Detection", "Time Series", "Big Data"]
}

# Flatten for easy lookup
ALL_SKILLS = set()
for cat, skills in SKILL_ONTOLOGY.items():
    ALL_SKILLS.update(skills)

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using PyMuPDF with optional pdfplumber fallback. Also supports .txt."""
    if pdf_path.lower().endswith('.txt'):
        try:
            with open(pdf_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read().strip()
        except Exception as e:
            warnings.warn(f"txt read failed: {e}", RuntimeWarning)
            return ""
    
    text = ""
    try:
        # Method 1: PyMuPDF (good for layout)
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text("text") + "\n"
        doc.close()
    except Exception as e:
        warnings.warn(f"PyMuPDF failed: {e}", RuntimeWarning)
    
    if len(text.strip()) < 100:  # Fallback if poor extraction
        if pdfplumber is None:
            warnings.warn(PDFPLUMBER_MISSING_MESSAGE, RuntimeWarning)
        else:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                warnings.warn(f"pdfplumber failed: {e}", RuntimeWarning)
    
    return text.strip()

def extract_email(text: str) -> Optional[str]:
    """Extract email using regex."""
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else None

def extract_name(text: str) -> Optional[str]:
    """Extract name using heuristics + spaCy NER."""
    lines = [l.strip() for l in text.split('\n')[:12] if l.strip()]
    for line in lines:
        # Skip obvious non-name lines
        if any(skip in line.lower() for skip in ["email", "phone", "linkedin", "location", "summary", "experience", "skills", "education", "project"]):
            continue
        if len(line) > 3 and len(line) < 45 and not any(char.isdigit() for char in line):
            # Title case or ALL CAPS names
            if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+$', line) or (line.isupper() and len(line.split()) >= 2):
                name = re.sub(r'\s*(Resume|CV|Curriculum Vitae|LinkedIn|Email|Phone|Github).*$', '', line, flags=re.IGNORECASE).strip()
                if len(name.split()) >= 2 and len(name) > 4:
                    return name
    
    # Fallback to spaCy PERSON
    doc = nlp(text[:2500])
    for ent in doc.ents:
        if ent.label_ == "PERSON" and len(ent.text.split()) >= 2 and len(ent.text) < 40:
            return ent.text.strip()
    return None

def extract_phone(text: str) -> Optional[str]:
    """Extract phone number."""
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    matches = re.findall(phone_pattern, text)
    return matches[0] if matches else None

def extract_skills(text: str) -> List[str]:
    """Extract skills using ontology matching + spaCy. Cleaned for noise."""
    text_lower = text.lower()
    found_skills = set()
    
    # Direct ontology match (case insensitive, whole word-ish)
    for skill in ALL_SKILLS:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.add(skill)
    
    # Additional spaCy noun chunks for potential skills (bonus) - filter aggressively
    doc = nlp(text[:3000])  # limit for speed
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.strip().title()
        if 3 < len(chunk_text) < 35:
            chunk_lower = chunk_text.lower()
            # Only add if closely matches ontology or strong indicators
            if (any(kw in chunk_lower for kw in ["python", "tensorflow", "pytorch", "aws", "nlp", "machine learning", "data science", "scikit", "hugging"]) 
                or chunk_text in ALL_SKILLS):
                found_skills.add(chunk_text)
    
    # Clean common junk from extraction (newlines, titles etc)
    cleaned = []
    for s in found_skills:
        s = re.sub(r'[\n\r]+', ' ', s).strip()
        s = re.sub(r'\s+', ' ', s)
        if len(s) > 2 and not any(bad in s.lower() for bad in ["resume", "cv", "email", "phone", "senior", "engineer", "candidate"]):
            cleaned.append(s)
    
    return sorted(list(set(cleaned)))[:20]  # cap

def extract_education(text: str) -> str:
    """Extract education using regex and heuristics."""
    edu_keywords = ["B.Tech", "B.E", "Bachelor", "M.Tech", "M.S", "Master", "PhD", "B.Sc", "M.Sc", "BCA", "MCA", "IIT", "NIT", "University", "College"]
    lines = text.split('\n')
    edu_lines = []
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(kw.lower() in line_lower for kw in edu_keywords):
            # Capture 1-2 lines around it
            edu_lines.append(line.strip())
            if i+1 < len(lines):
                edu_lines.append(lines[i+1].strip())
            break
    
    if edu_lines:
        return " | ".join(edu_lines[:2])
    
    # Fallback regex
    edu_pattern = r'(B\.?Tech|M\.?Tech|B\.?E\.?|M\.?S\.?|Bachelor|Master|Ph\.?D)\s*[^,\n]+'
    match = re.search(edu_pattern, text, re.IGNORECASE)
    return match.group(0).strip() if match else "Not specified"

def extract_experience_years(text: str) -> int:
    """Estimate total experience years from text. More robust."""
    # Look for patterns like "X years", "X+ years"
    year_pattern = r'(\d+)\s*(?:\+|plus)?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp|work)'
    matches = re.findall(year_pattern, text, re.IGNORECASE)
    if matches:
        return max(int(m) for m in matches)
    
    # Date ranges e.g. 2020 - Present , Jan 2022 - 2024
    date_pattern = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s*(\d{4})\s*[-–]\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s*(\d{4}|Present|Current|Now)'
    date_matches = re.findall(date_pattern, text, re.IGNORECASE)
    if date_matches:
        total = 0
        for start, end in date_matches:
            try:
                s = int(start)
                e = 2026 if end.lower() in ['present', 'current', 'now'] else int(end)
                total += max(0, e - s)
            except:
                pass
        if total > 0:
            return min(total, 25)
    
    # Heuristic from number of jobs / roles
    job_indicators = len(re.findall(r'(?:Engineer|Scientist|Analyst|Developer|Manager|Lead)\s*(?:\| | at |, | - )', text, re.IGNORECASE))
    if job_indicators >= 3:
        return 5
    elif job_indicators >= 2:
        return 3
    elif "senior" in text.lower() or "lead" in text.lower():
        return 4
    return 2  # default

def extract_projects(text: str) -> List[str]:
    """Extract project titles."""
    projects = []
    # Look for PROJECTS section
    project_section = re.search(r'PROJECTS?\s*[:\n](.*?)(?:\n\s*(?:EDUCATION|CERTIF|SKILLS|EXPERIENCE)|$)', text, re.IGNORECASE | re.DOTALL)
    
    if project_section:
        section_text = project_section.group(1)
        # Extract bullet points or lines starting with -
        bullets = re.findall(r'[-•]\s*([^\n]+)', section_text)
        projects.extend([b.strip() for b in bullets if len(b.strip()) > 5][:5])
    
    if not projects:
        # Fallback: look for common project names
        common = ["Fraud Detection", "Brain Tumor", "Recommendation", "Chatbot", "RAG", "NLP", "Computer Vision", "Sentiment", "Dashboard"]
        for c in common:
            if c.lower() in text.lower():
                projects.append(c)
    
    return projects[:5] if projects else ["Not specified"]

def extract_structured_resume(pdf_path: str) -> Dict[str, Any]:
    """Main function: Parse PDF and return structured candidate data."""
    text = extract_text_from_pdf(pdf_path)
    
    if not text or len(text) < 50:
        return {
            "name": "Unknown",
            "email": None,
            "phone": None,
            "skills": [],
            "education": "Not extracted",
            "experience_years": 0,
            "projects": [],
            "raw_text": text[:500] + "...",
            "error": "Insufficient text extracted"
        }
    
    candidate = {
        "name": extract_name(text) or "Unknown Candidate",
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "education": extract_education(text),
        "experience_years": extract_experience_years(text),
        "projects": extract_projects(text),
        "raw_text": text[:2000] + "..." if len(text) > 2000 else text,
        "file_path": pdf_path
    }
    
    return candidate

def batch_parse_resumes(resume_paths: List[str]) -> List[Dict[str, Any]]:
    """Parse multiple resumes."""
    results = []
    for path in resume_paths:
        try:
            parsed = extract_structured_resume(path)
            results.append(parsed)
        except Exception as e:
            warnings.warn(f"Error parsing {path}: {e}", RuntimeWarning)
            results.append({
                "name": os.path.basename(path),
                "email": None,
                "skills": [],
                "education": "Parse error",
                "experience_years": 0,
                "projects": [],
                "error": str(e)
            })
    return results

if __name__ == "__main__":
    # Test with sample
    sample = "/home/user/ai-recruiter/data/resumes/john_doe_strong_match.pdf"
    if os.path.exists(sample):
        result = extract_structured_resume(sample)
        print(json.dumps(result, indent=2))
