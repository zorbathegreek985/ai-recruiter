"""Candidate PDF report generation."""
import os
import re
from typing import Any, Dict, Optional

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None


def _clean(text: Any) -> str:
    value = str(text or "")
    return value.encode("latin-1", "replace").decode("latin-1")


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", name or "candidate").strip("_")
    return cleaned or "candidate"


def create_candidate_pdf_report(
    candidate: Dict[str, Any],
    jd: Dict[str, Any],
    score_evidence: Dict[str, Any],
    gap_report: Dict[str, Any],
    interview_plan: Dict[str, Any],
    output_dir: Optional[str] = None,
) -> str:
    """Create a recruiter-ready candidate PDF and return the file path."""
    if FPDF is None:
        raise RuntimeError("PDF generation requires fpdf2. Install fpdf2 to enable downloadable reports.")

    output_dir = output_dir or os.path.join(os.getcwd(), "reports", "generated")
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, _safe_filename(candidate.get("name", "candidate")) + "_report.pdf")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _clean("AI Recruiter Candidate Report"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 7, _clean(f"Candidate: {candidate.get('name', 'Unknown')}"))
    pdf.multi_cell(0, 7, _clean(f"Role: {jd.get('role_category', 'Role not specified')}"))
    pdf.multi_cell(0, 7, _clean(f"Overall Score: {score_evidence.get('overall', 0)}"))

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, _clean("Recommendation"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    hiring = candidate.get("hiring_recommendation", {})
    pdf.multi_cell(0, 6, _clean(f"Decision: {hiring.get('recommendation', 'Review')}"))
    pdf.multi_cell(0, 6, _clean(f"Confidence: {hiring.get('confidence_score', 0)}"))
    pdf.multi_cell(0, 6, _clean("Strengths: " + ", ".join(hiring.get("strengths", [])[:5])))
    pdf.multi_cell(0, 6, _clean("Weaknesses: " + ", ".join(hiring.get("weaknesses", [])[:5])))

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, _clean("Explainable Scoring"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for dimension in score_evidence.get("dimensions", []):
        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(
            0,
            6,
            _clean(f"{dimension['dimension']}: {dimension['score']} (weighted {dimension['weighted_contribution']})"),
        )
        pdf.set_font("Helvetica", "", 9)
        for evidence in dimension.get("evidence", [])[:4]:
            pdf.multi_cell(0, 5, _clean(f"- {evidence}"))

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, _clean("Skill Gap Analysis"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, _clean(gap_report.get("summary", "")))
    for gap in gap_report.get("priority_gaps", [])[:8]:
        pdf.multi_cell(0, 5, _clean(f"- {gap['skill']} ({gap['severity']}): {gap['recommendation']}"))

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, _clean("Interview Plan"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for question in interview_plan.get("questions", [])[:8]:
        pdf.multi_cell(0, 5, _clean(f"- [{question['type']}] {question['question']}"))

    pdf.output(path)
    return path
