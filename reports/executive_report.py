"""Executive PDF report for the full recruiting batch."""
import os
from typing import Any, Dict, List, Optional

from reports.pdf_report import _clean

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None


def create_executive_pdf_report(
    jd: Dict[str, Any],
    ranked_candidates: List[Dict[str, Any]],
    output_dir: Optional[str] = None,
) -> str:
    """Create a hackathon-ready executive report PDF for the full batch."""
    if FPDF is None:
        raise RuntimeError("Executive PDF generation requires fpdf2. Install fpdf2 to enable downloadable reports.")

    output_dir = output_dir or os.path.join(os.getcwd(), "reports", "generated")
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "executive_talent_intelligence_report.pdf")

    top_candidates = ranked_candidates[:5]
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 17)
    pdf.cell(0, 10, _clean("AI Recruiter Executive Talent Intelligence Report"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, _clean(f"Role: {jd.get('role_category', 'Not specified')}"))
    pdf.multi_cell(0, 6, _clean(f"Required Skills: {', '.join(jd.get('required_skills', [])) or 'Not specified'}"))
    pdf.multi_cell(0, 6, _clean(f"Preferred Skills: {', '.join(jd.get('preferred_skills', [])) or 'Not specified'}"))
    pdf.multi_cell(0, 6, _clean(f"Experience: {jd.get('experience', 'Not specified')}"))

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, _clean("Top Candidates and Recommendations"), new_x="LMARGIN", new_y="NEXT")
    for candidate in top_candidates:
        hiring = candidate.get("hiring_recommendation", {})
        risk = candidate.get("risk_report", {})
        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(
            0,
            6,
            _clean(
                f"#{candidate.get('rank')} {candidate.get('name', 'Unknown')} - "
                f"{candidate.get('overall_score', 0)}% - {hiring.get('recommendation', 'Review')}"
            ),
        )
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, _clean("Strengths: " + ", ".join(hiring.get("strengths", [])[:3])))
        pdf.multi_cell(0, 5, _clean("Risks: " + ", ".join(hiring.get("risks", [risk.get("risk_level", "Low")])[:3])))

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, _clean("Interview Questions"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    for candidate in top_candidates[:3]:
        plan = candidate.get("interview_plan", {})
        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(0, 6, _clean(candidate.get("name", "Candidate")))
        pdf.set_font("Helvetica", "", 9)
        for question in plan.get("questions", [])[:4]:
            pdf.multi_cell(0, 5, _clean(f"- [{question.get('type')}] {question.get('question')}"))

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, _clean("Skill Gap and Learning Roadmap"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    for candidate in top_candidates:
        gap = candidate.get("advanced_skill_gap", {})
        growth = candidate.get("career_growth_plan", {})
        pdf.multi_cell(
            0,
            5,
            _clean(
                f"{candidate.get('name', 'Candidate')}: {gap.get('summary', 'No summary')} "
                f"Projected: {growth.get('projected_match_score', candidate.get('overall_score', 0))}%"
            ),
        )

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, _clean("Analytics Snapshot"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    avg_score = round(sum(c.get("overall_score", 0) for c in ranked_candidates) / max(1, len(ranked_candidates)), 1)
    avg_risk = round(
        sum(c.get("risk_report", {}).get("risk_score", 0) for c in ranked_candidates) / max(1, len(ranked_candidates)),
        1,
    )
    pdf.multi_cell(0, 5, _clean(f"Candidates analyzed: {len(ranked_candidates)}"))
    pdf.multi_cell(0, 5, _clean(f"Average match score: {avg_score}%"))
    pdf.multi_cell(0, 5, _clean(f"Average resume risk score: {avg_risk}"))

    pdf.output(path)
    return path
