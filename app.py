"""
AI Recruiter - Main Streamlit Application
Intelligent Candidate Discovery & Ranking
"""
import streamlit as st
import os
import tempfile
import pandas as pd
from typing import List, Dict, Any
import json

# Import all modules
from parsers.resume_parser import (
    batch_parse_resumes,
    extract_structured_resume,
    get_optional_dependency_warnings as get_resume_parser_warnings,
)
from parsers.jd_parser import get_optional_dependency_warnings as get_jd_parser_warnings
from agents import analyze_jd, rank_candidates_with_agents
from agents.career_growth_agent import generate_growth_plan
from agents.fairness_agent import build_fairness_dashboard
from explainability.explanation_engine import (
    generate_explanation, generate_skill_gap_analysis, 
    generate_interview_questions
)
from rag.faiss_search import vector_store
from dashboard.analytics import (
    create_ranking_distribution_chart, create_score_breakdown_chart,
    create_top_skills_chart, create_skill_gap_frequency_chart,
    create_average_match_gauge, get_summary_stats
)
from dashboard.recruiter_dashboard import (
    build_batch_summary,
    build_candidate_decision_table,
    compare_candidates,
    filter_candidates,
    sort_candidates,
)
from embeddings.embedding_engine import semantic_similarity
from explainability.scoring_explainer import build_score_evidence
from explainability.skill_gap_engine import build_advanced_skill_gap
from reports.pdf_report import create_candidate_pdf_report
from reports.executive_report import create_executive_pdf_report
from agents.bias_agent import analyze_bias_signals
from agents.github_agent import analyze_github_profile
from agents.interview_agent import generate_interview_plan

# Page config
st.set_page_config(
    page_title="AI Recruiter | Intelligent Candidate Ranking",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better look
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: 750; color: #12355b; margin-bottom: 0.2rem;}
    .score-badge {padding: 4px 12px; border-radius: 20px; font-weight: 600;}
    .high-score {background-color: #d4edda; color: #155724;}
    .medium-score {background-color: #fff3cd; color: #856404;}
    .low-score {background-color: #f8d7da; color: #721c24;}
    .stApp {background: #f7f9fc;}
    .block-container {padding-top: 1.5rem;}
    .stTabs [data-baseweb="tab-list"] {gap: 8px; flex-wrap: wrap;}
    .candidate-card {
        border: 1px solid #d9e2ec;
        border-radius: 8px;
        padding: 16px;
        margin: 10px 0;
        background: #ffffff;
        box-shadow: 0 1px 3px rgba(16, 24, 40, 0.08);
    }
    .agent-card {
        border: 1px solid #d9e2ec;
        border-left: 5px solid #1f77b4;
        border-radius: 8px;
        padding: 16px;
        background: #ffffff;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(16, 24, 40, 0.08);
    }
    .agent-card h3 {margin: 0 0 6px 0; color: #102a43;}
    .subtle {color: #52616b; font-size: 0.92rem;}
    .pill {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 999px;
        background: #e6f4ff;
        color: #0b5394;
        font-size: 0.82rem;
        font-weight: 650;
        margin-right: 6px;
    }
</style>
""", unsafe_allow_html=True)


def safe_plotly_chart(fig, **kwargs):
    if fig is None:
        st.info("Charts are unavailable because Plotly is not installed in this environment.")
    else:
        st.plotly_chart(fig, **kwargs)


def render_list(items: List[str], empty: str = "None detected"):
    if not items:
        st.write(empty)
    for item in items:
        st.write(f"- {item}")


def load_samples():
    """Load the pre-generated sample data (prefers clean .txt for reliable demo parsing)."""
    jd_path = "data/jd/ml_engineer_jd.txt"
    resume_paths = [
        "data/resumes/john_doe_strong_match.txt",
        "data/resumes/alice_chen_nlp.txt",
        "data/resumes/jane_smith_medium.txt",
        "data/resumes/bob_johnson_weaker.txt"
    ]

    with st.spinner("Loading and parsing sample data..."):
        jd = analyze_jd(jd_path)
        st.session_state.jd_data = jd

        parsed = batch_parse_resumes(resume_paths)
        st.session_state.candidates = parsed

        ranked = rank_candidates_with_agents(parsed, jd)
        st.session_state.ranked_candidates = ranked

        vector_store.candidates = []
        vector_store.embeddings = []
        vector_store.add_candidates(parsed)
        st.session_state.vector_store_loaded = True

    st.success("Sample data loaded! Explore the tabs below.")
    st.rerun()


optional_dependency_warnings = sorted(
    set(get_resume_parser_warnings() + get_jd_parser_warnings())
)
for warning in optional_dependency_warnings:
    st.warning(warning)

# Session state initialization
if "jd_data" not in st.session_state:
    st.session_state.jd_data = None
if "candidates" not in st.session_state:
    st.session_state.candidates = []
if "ranked_candidates" not in st.session_state:
    st.session_state.ranked_candidates = []
if "vector_store_loaded" not in st.session_state:
    st.session_state.vector_store_loaded = False

# Load API key: prefer Streamlit secrets (for cloud) then env var
def get_api_key():
    key = ""
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            key = st.secrets["GOOGLE_API_KEY"]
    except Exception:
        pass
    if not key:
        key = os.getenv("GOOGLE_API_KEY", "")
    return key

if "gemini_key" not in st.session_state:
    st.session_state.gemini_key = get_api_key()

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key - supports Streamlit secrets on cloud + manual input
    current_key = st.session_state.gemini_key
    if current_key:
        st.success("✅ Gemini API key loaded (from secrets or env)")
    
    api_key = st.text_input(
        "Google Gemini API Key (optional for demo)",
        value="",
        type="password",
        help="Get free key at https://aistudio.google.com/app/apikey. On Streamlit Cloud, set in Secrets instead of here."
    )
    if api_key:
        st.session_state.gemini_key = api_key
        os.environ["GOOGLE_API_KEY"] = api_key
        # Re-configure
        import google.generativeai as genai
        try:
            genai.configure(api_key=api_key)
            st.success("✅ Gemini API key set for this session")
        except:
            st.warning("Invalid key format")
    
    st.divider()
    
    st.subheader("Ranking Weights")
    w_skill = st.slider("Skill Match", 0.0, 1.0, 0.45, 0.05)
    w_exp = st.slider("Experience", 0.0, 1.0, 0.30, 0.05)
    w_proj = st.slider("Projects", 0.0, 1.0, 0.15, 0.05)
    w_edu = st.slider("Education", 0.0, 1.0, 0.10, 0.05)
    
    if st.button("Update Weights"):
        from ranking.ranking_engine import WEIGHTS
        WEIGHTS["skill_match"] = w_skill
        WEIGHTS["experience"] = w_exp
        WEIGHTS["projects"] = w_proj
        WEIGHTS["education"] = w_edu
        st.success("Weights updated! Re-rank to apply.")
    
    st.divider()
    
    # Load sample data button
    if st.button("📥 Load Sample Dataset (4 candidates + JD)", type="primary"):
        load_samples()

# Main Header
st.markdown('<h1 class="main-header">🤖 AI Recruiter</h1>', unsafe_allow_html=True)
st.caption("Intelligent Candidate Discovery & Ranking using Semantic AI • Explainable • Production Ready")

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📄 Job Description", 
    "📁 Resumes & Ranking", 
    "🔍 Recruiter Search (RAG)", 
    "📊 Analytics", 
    "🔎 Skill Gaps & Insights",
    "💬 AI Chatbot & Tools",
    "AI Interview Agent",
    "Reports & Fairness",
    "Batch & GitHub"
])

# ============ TAB 1: JD ============
with tab1:
    st.header("Job Description Upload & Parsing")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        jd_file = st.file_uploader(
            "Upload JD PDF or Text file",
            type=["pdf", "txt", "md"],
            key="jd_uploader"
        )
        
        jd_text_input = st.text_area(
            "Or paste JD text here",
            height=200,
            placeholder="Senior Machine Learning Engineer\nRequired: Python, TensorFlow, AWS..."
        )
        
        if st.button("Parse Job Description", type="primary"):
            with st.spinner("Parsing JD..."):
                if jd_file:
                    # Save temp
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf" if jd_file.name.endswith('.pdf') else ".txt") as tmp:
                        tmp.write(jd_file.getvalue())
                        tmp_path = tmp.name
                    
                    if jd_file.name.endswith('.pdf'):
                        jd = analyze_jd(tmp_path)
                    else:
                        jd = analyze_jd(jd_text_input or jd_file.getvalue().decode())
                    os.unlink(tmp_path)
                elif jd_text_input.strip():
                    jd = analyze_jd(jd_text_input)
                else:
                    st.error("Please upload a file or paste text.")
                    jd = None
                
                if jd:
                    st.session_state.jd_data = jd
                    st.success("JD parsed successfully!")
    
    with col2:
        if st.session_state.jd_data:
            jd = st.session_state.jd_data
            st.subheader("📋 Extracted JD Information")
            
            st.markdown(f"**Role Category:** {jd.get('role_category', 'N/A')}")
            st.markdown(f"**Industry / Domain:** {jd.get('industry_domain', 'N/A')}")
            st.markdown(f"**Experience Required:** {jd.get('experience', 'N/A')}")
            st.markdown(f"**Education:** {jd.get('education', 'N/A')[:100]}")
            
            st.markdown("**Required Skills:**")
            st.write(", ".join(jd.get("required_skills", [])) or "None extracted")
            
            st.markdown("**Preferred Skills:**")
            st.write(", ".join(jd.get("preferred_skills", [])) or "None")
            
            with st.expander("View Raw Text"):
                st.text(jd.get("raw_text", "")[:800])
        else:
            st.info("Upload or paste a JD and click Parse to begin.")

# ============ TAB 2: Resumes & Ranking ============
with tab2:
    st.header("Resume Upload, Parsing & Ranking")
    
    uploaded_files = st.file_uploader(
        "Upload multiple resumes (PDF, TXT, or Markdown)",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True,
        key="resume_uploader"
    )
    
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        if st.button("Process & Rank Candidates", disabled=not (uploaded_files or st.session_state.candidates), type="primary"):
            if not st.session_state.jd_data:
                st.error("Please parse a Job Description first (Tab 1).")
            else:
                with st.spinner("Parsing resumes and computing rankings..."):
                    parsed_cands = []
                    
                    if uploaded_files:
                        for uploaded_file in uploaded_files:
                            suffix = os.path.splitext(uploaded_file.name)[1].lower() or ".txt"
                            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                                tmp.write(uploaded_file.getvalue())
                                tmp_path = tmp.name
                            
                            try:
                                parsed = extract_structured_resume(tmp_path)
                                parsed["source_file"] = uploaded_file.name
                                parsed_cands.append(parsed)
                            except Exception as e:
                                st.error(f"Failed to parse {uploaded_file.name}: {e}")
                            finally:
                                os.unlink(tmp_path)
                    else:
                        parsed_cands = st.session_state.candidates
                    
                    if parsed_cands:
                        st.session_state.candidates = parsed_cands
                        
                        # Rank
                        ranked = rank_candidates_with_agents(parsed_cands, st.session_state.jd_data)
                        st.session_state.ranked_candidates = ranked
                        
                        # Update vector store
                        vector_store.candidates = []
                        vector_store.embeddings = []
                        vector_store.add_candidates(parsed_cands)
                        st.session_state.vector_store_loaded = True
                        
                        st.success(f"✅ Processed and ranked {len(ranked)} candidates!")
    
    with col_b:
        if st.session_state.ranked_candidates:
            st.subheader(f"🏆 Ranked Candidates ({len(st.session_state.ranked_candidates)})")
            
            # Summary table
            table_data = []
            for cand in st.session_state.ranked_candidates:
                scores = cand.get("scores", {})
                table_data.append({
                    "Rank": cand.get("rank", 0),
                    "Name": cand.get("name", "Unknown")[:25],
                    "Overall": f"{cand.get('overall_score', 0):.1f}%",
                    "Skills": f"{scores.get('skill_match', 0):.0f}%",
                    "Exp": f"{scores.get('experience', 0):.0f}%",
                    "Projects": f"{scores.get('projects', 0):.0f}%",
                    "Edu": f"{scores.get('education', 0):.0f}%",
                    "Exp Yrs": cand.get("experience_years", 0),
                    "Skills Count": len(cand.get("skills", []))
                })
            
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Detailed cards
            st.markdown("### Detailed View")
            for cand in st.session_state.ranked_candidates[:6]:  # Limit display
                with st.expander(f"#{cand['rank']} {cand['name']} — Overall: {cand['overall_score']:.1f}%"):
                    cols = st.columns([2, 1, 1])
                    
                    with cols[0]:
                        st.write("**Skills:**", ", ".join(cand.get("skills", [])[:10]) or "N/A")
                        st.write("**Projects:**", " | ".join(cand.get("projects", [])[:3]) or "N/A")
                        st.write("**Certifications:**", ", ".join(cand.get("certifications", [])[:4]) or "N/A")
                        st.write("**Education:**", cand.get("education", "N/A")[:80])
                        st.write("**Email:**", cand.get("email", "N/A"))
                    
                    with cols[1]:
                        scores = cand.get("scores", {})
                        st.metric("Overall", f"{scores.get('overall', 0):.1f}")
                        st.metric("Skill Match", f"{scores.get('skill_match', 0):.1f}")
                        st.metric("Experience", f"{scores.get('experience', 0):.1f}")
                    
                    with cols[2]:
                        st.metric("Projects", f"{scores.get('projects', 0):.1f}")
                        st.metric("Education", f"{scores.get('education', 0):.1f}")
                        st.metric("Years Exp", cand.get("experience_years", 0))

                    hiring = cand.get("hiring_recommendation", {})
                    match = cand.get("agent_analysis", {}).get("match", {})
                    risk = cand.get("risk_report", {})
                    if hiring:
                        st.info(
                            f"**Hiring Agent:** {hiring.get('recommendation', 'N/A')} "
                            f"| Confidence: {hiring.get('confidence_score', 0):.1f}% "
                            f"| Semantic Fit: {match.get('semantic_fit', 0):.1f}% "
                            f"| Risk: {risk.get('risk_level', 'N/A')}"
                        )
                    
                    # Explanation
                    explanation = generate_explanation(
                        cand, st.session_state.jd_data, 
                        cand.get("scores", {}), cand.get("rank", 0)
                    )
                    st.markdown(f"**AI Explanation:** {explanation}")
                    
                    # Skill gap quick
                    gaps = generate_skill_gap_analysis(cand, st.session_state.jd_data)
                    if gaps["missing_skills"]:
                        st.warning(f"**Missing:** {', '.join(gaps['missing_skills'][:4])}")
                    else:
                        st.success("No major skill gaps!")
                    
                    # Interview questions button
                    if st.button(f"Generate Interview Qs for {cand['name']}", key=f"iq_{cand['rank']}"):
                        questions = generate_interview_questions(cand, st.session_state.jd_data)
                        st.write("**Suggested Interview Questions:**")
                        for i, q in enumerate(questions, 1):
                            st.write(f"{i}. {q}")
        else:
            st.info("Upload resumes and click 'Process & Rank' (or load samples from sidebar).")

# ============ TAB 3: RAG Search ============
with tab3:
    st.header("🔍 Natural Language Recruiter Search (RAG + FAISS)")
    st.caption("Ask in plain English. Powered by semantic embeddings + vector search.")
    
    if not st.session_state.vector_store_loaded or not st.session_state.ranked_candidates:
        st.warning("Please process some candidates first (Tab 2) to enable search.")
    else:
        example_queries = [
            "Find candidates with NLP experience",
            "Show candidates with Python and TensorFlow",
            "Candidates suitable for ML Engineer roles with AWS",
            "People who have worked on RAG or LLM projects",
            "Strong Python developers with 3+ years ML exp"
        ]
        
        query = st.selectbox("Try an example query:", example_queries, index=0) or \
                st.text_input("Or type your own recruiter query:", placeholder="Find candidates with experience in LLMs and production ML systems")
        
        top_k = st.slider("Number of results", 1, 10, 5)
        
        if st.button("Search Candidates", type="primary"):
            with st.spinner("Performing semantic search..."):
                results = vector_store.search(query, top_k=top_k)
            
            if results:
                st.subheader(f"Top {len(results)} Matches for: *{query}*")
                
                for i, res in enumerate(results, 1):
                    sim = res.get("search_similarity", 0)
                    score_color = "🟢" if sim > 0.75 else "🟡" if sim > 0.55 else "🔴"
                    
                    st.markdown(f"""
                    **{i}. {res.get('name', 'Unknown')}** {score_color} Similarity: **{sim:.2f}**
                    - Skills: {', '.join(res.get('skills', [])[:6])}
                    - Experience: {res.get('experience_years', 0)} years
                    - Key Projects: {', '.join(res.get('projects', [])[:2])}
                    """)
                    
                    # Link to full profile if in ranked
                    matching_ranked = [c for c in st.session_state.ranked_candidates if c.get("name") == res.get("name")]
                    if matching_ranked:
                        st.caption(f"Overall Rank in JD: #{matching_ranked[0].get('rank')} | Score: {matching_ranked[0].get('overall_score')}%")
            else:
                st.info("No strong matches found. Try broadening the query.")

# ============ TAB 4: Analytics ============
with tab4:
    st.header("📊 Analytics Dashboard")
    
    if not st.session_state.ranked_candidates:
        st.info("Process candidates to see analytics.")
    else:
        ranked = st.session_state.ranked_candidates
        jd = st.session_state.jd_data or {}
        
        stats = get_summary_stats(ranked)
        batch_summary = build_batch_summary(ranked)
        
        # KPI cards
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total Candidates", stats["total"])
        kpi2.metric("Avg Match Score", f"{stats['avg_score']}%")
        kpi3.metric("Top Score", f"{stats['top_score']}%")
        kpi4.metric("High Match (≥80%)", stats["high_match"])

        st.subheader("Recruiter Decision Dashboard")
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Strong Hire", batch_summary["strong_hires"])
        d2.metric("Interview Ready", batch_summary["interview_ready"])
        d3.metric("Needs Review", batch_summary["needs_review"])
        d4.metric("Avg Risk", batch_summary["avg_risk"])

        search_col, score_col, risk_col, sort_col = st.columns(4)
        with search_col:
            dashboard_query = st.text_input("Search candidates", key="dashboard_search")
        with score_col:
            min_dashboard_score = st.slider("Minimum score", 0, 100, 0, 5, key="dashboard_min_score")
        with risk_col:
            max_dashboard_risk = st.selectbox("Maximum risk", ["High", "Medium", "Low"], key="dashboard_max_risk")
        with sort_col:
            dashboard_sort = st.selectbox(
                "Sort by",
                ["Overall", "Skill Match", "Experience", "Projects", "Education", "Lowest Risk"],
                key="dashboard_sort",
            )

        filtered_ranked = sort_candidates(
            filter_candidates(ranked, dashboard_query, min_dashboard_score, max_dashboard_risk),
            dashboard_sort,
        )
        decision_df = build_candidate_decision_table(filtered_ranked)
        st.dataframe(decision_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download shortlist CSV",
            decision_df.to_csv(index=False).encode("utf-8"),
            file_name="ai_recruiter_shortlist.csv",
            mime="text/csv",
        )

        compare_names = st.multiselect(
            "Compare candidates",
            [c["name"] for c in ranked],
            default=[c["name"] for c in ranked[: min(2, len(ranked))]],
            key="dashboard_compare",
        )
        compared = [c for c in ranked if c["name"] in compare_names]
        if compared:
            st.dataframe(compare_candidates(compared), use_container_width=True, hide_index=True)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            safe_plotly_chart(
                create_ranking_distribution_chart(ranked),
                use_container_width=True
            )
            safe_plotly_chart(
                create_average_match_gauge(ranked),
                use_container_width=True
            )
        
        with col2:
            safe_plotly_chart(
                create_top_skills_chart(ranked),
                use_container_width=True
            )
            if jd:
                safe_plotly_chart(
                    create_skill_gap_frequency_chart(ranked, jd),
                    use_container_width=True
                )
        
        # Individual breakdown selector
        st.subheader("Individual Score Breakdown")
        selected_name = st.selectbox(
            "Select candidate for detailed radar chart:",
            [c["name"] for c in ranked]
        )
        selected_cand = next((c for c in ranked if c["name"] == selected_name), None)
        if selected_cand:
            safe_plotly_chart(create_score_breakdown_chart(selected_cand), use_container_width=True)

# ============ TAB 5: Skill Gaps ============
with tab5:
    st.header("🔎 Skill Gap Analysis")
    
    if not st.session_state.ranked_candidates or not st.session_state.jd_data:
        st.info("Need JD + ranked candidates.")
    else:
        jd = st.session_state.jd_data
        ranked = st.session_state.ranked_candidates
        
        st.subheader("JD Requirements")
        st.write("**Required:**", ", ".join(jd.get("required_skills", [])))
        st.write("**Preferred:**", ", ".join(jd.get("preferred_skills", [])))
        
        st.divider()
        
        # Global gap summary
        st.subheader("Aggregate Skill Gaps")
        all_gaps = {}
        for cand in ranked:
            gaps = generate_skill_gap_analysis(cand, jd)
            for m in gaps["missing_skills"]:
                all_gaps[m] = all_gaps.get(m, 0) + 1
        
        if all_gaps:
            gap_df = pd.DataFrame(list(all_gaps.items()), columns=["Skill", "# Candidates Missing"]).sort_values("# Candidates Missing", ascending=False)
            st.dataframe(gap_df, use_container_width=True)
        else:
            st.success("All candidates cover the required skills well!")
        
        st.divider()
        
        # Per candidate
        st.subheader("Per-Candidate Gap Analysis")
        for cand in ranked:
            gaps = generate_skill_gap_analysis(cand, jd)
            match_pct = gaps["match_percentage"]
            
            color = "🟢" if match_pct >= 80 else "🟡" if match_pct >= 60 else "🔴"
            
            with st.expander(f"{color} {cand['name']} — Match: {match_pct}% | Rank #{cand['rank']}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.success("**Matched Skills**")
                    st.write(", ".join(gaps["matched_skills"]) or "None")
                with c2:
                    st.error("**Missing Skills**")
                    st.write(", ".join(gaps["missing_skills"]) or "None")
                
                st.caption(f"Matched {gaps['total_matched']}/{gaps['total_required']} required skills")

        st.divider()
        st.subheader("Priority Gap Recommendations")
        selected_gap_name = st.selectbox(
            "Select candidate for prioritized gap plan:",
            [c["name"] for c in ranked],
            key="priority_gap_select",
        )
        selected_gap_candidate = next((c for c in ranked if c["name"] == selected_gap_name), None)
        if selected_gap_candidate:
            advanced_gap = selected_gap_candidate.get("advanced_skill_gap") or build_advanced_skill_gap(selected_gap_candidate, jd)
            st.metric("Required Skill Coverage", f"{advanced_gap['coverage']}%")
            st.info(advanced_gap["summary"])
            if advanced_gap["priority_gaps"]:
                st.dataframe(pd.DataFrame(advanced_gap["priority_gaps"]), use_container_width=True, hide_index=True)
            else:
                st.success("No priority gaps detected for this JD.")
            if advanced_gap.get("recommended_learning_path"):
                st.write("**Recommended Learning Path**")
                st.dataframe(
                    pd.DataFrame(advanced_gap["recommended_learning_path"]),
                    use_container_width=True,
                    hide_index=True,
                )
            growth_plan = selected_gap_candidate.get("career_growth_plan") or generate_growth_plan(selected_gap_candidate, jd)
            st.write("**Career Growth Roadmap**")
            g1, g2 = st.columns(2)
            g1.metric("Current Match", f"{growth_plan['current_match_score']}%")
            g2.metric("Projected Match", f"{growth_plan['projected_match_score']}%")
            st.caption(growth_plan["summary"])
            st.dataframe(pd.DataFrame(growth_plan["roadmap"]), use_container_width=True, hide_index=True)

# ============ TAB 6: Bonus Tools ============
with tab6:
    st.header("💬 AI-Powered Recruiter Tools (Bonus Features)")
    
    if not st.session_state.ranked_candidates:
        st.info("Load candidates to use these tools.")
    else:
        ranked = st.session_state.ranked_candidates
        
        # 1. Interview Question Generator
        st.subheader("🎯 Interview Question Generator")
        sel_cand_name = st.selectbox("Select candidate", [c["name"] for c in ranked], key="iq_select")
        sel_cand = next(c for c in ranked if c["name"] == sel_cand_name)
        
        num_q = st.slider("Number of questions", 3, 8, 5, key="num_q")
        if st.button("Generate Questions"):
            qs = generate_interview_questions(sel_cand, st.session_state.jd_data or {}, num_q)
            for i, q in enumerate(qs, 1):
                st.write(f"**Q{i}:** {q}")
        
        st.divider()
        
        # 2. Simple Recruiter Chatbot (using Gemini)
        st.subheader("🤖 LLM Recruiter Chatbot")
        st.caption("Ask anything about the current candidates or JD. Powered by Gemini.")
        
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        user_query = st.text_input("Ask the AI Recruiter:", placeholder="Which candidate has the best NLP experience? Summarize top 2 candidates.")
        
        if st.button("Send") and user_query:
            if not (st.session_state.gemini_key or os.getenv("GOOGLE_API_KEY")):
                st.warning("Please set Gemini API key in sidebar (or via Streamlit Secrets on cloud) for the chatbot.")
            else:
                try:
                    import google.generativeai as genai
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    context = "Current JD: " + str(st.session_state.jd_data)[:400] + "\n\n"
                    context += "Top Candidates:\n"
                    for c in ranked[:3]:
                        context += f"- {c['name']}: Score {c['overall_score']}, Skills: {c.get('skills', [])[:5]}, Exp: {c.get('experience_years')}y\n"
                    
                    full_prompt = f"""You are a helpful AI Recruiter assistant. Use the provided context about the job and candidates to answer the question accurately and concisely.

{context}

User question: {user_query}

Answer:"""
                    
                    resp = model.generate_content(full_prompt)
                    answer = resp.text
                    
                    st.session_state.chat_history.append(("You", user_query))
                    st.session_state.chat_history.append(("AI", answer))
                except Exception as e:
                    st.error(f"Chatbot error: {e}")
        
        # Display chat
        for role, msg in st.session_state.chat_history[-6:]:
            if role == "You":
                st.markdown(f"**You:** {msg}")
            else:
                st.markdown(f"**AI Recruiter:** {msg}")
        
        st.divider()
        
        # 3. Basic Fraud & Duplicate Detection
        st.subheader("🕵️ Fraud & Duplicate Detection (Basic)")
        
        if st.button("Run Fraud & Duplicate Scan"):
            fraud_reports = []
            duplicate_pairs = []

            for c1 in ranked:
                risk = c1.get("risk_report", {})
                for duplicate in risk.get("duplicates", []):
                    duplicate_pairs.append((duplicate["candidate_a"], duplicate["candidate_b"], duplicate["reason"]))

                reasons = []
                keyword_report = risk.get("keyword_stuffing", {})
                if keyword_report.get("detected"):
                    keywords = [
                        f"{signal['keyword']} ({signal['count']}x)"
                        for signal in keyword_report.get("signals", [])[:3]
                    ]
                    reasons.append("Keyword stuffing signals: " + ", ".join(keywords))

                reasons.extend(risk.get("anomalies", {}).get("reasons", []))

                if risk.get("risk_score", 0) > 25:
                    fraud_reports.append({
                        "name": c1["name"],
                        "score": risk.get("risk_score", 0),
                        "level": risk.get("risk_level", "Low"),
                        "reasons": reasons
                    })
            
            if duplicate_pairs:
                st.warning("**Possible Duplicates Found:**")
                for p in set(duplicate_pairs):
                    st.write(f"- {p[0]} and {p[1]} ({p[2]})")
            else:
                st.success("No obvious duplicates detected.")
            
            if fraud_reports:
                st.error("**Potential Fraud / Low-Quality Resumes:**")
                for f in fraud_reports:
                    st.write(f"• **{f['name']}** ({f['level']} Risk: {f['score']}) — {', '.join(f['reasons'])}")
            else:
                st.success("No obvious fraud signals detected in current batch.")
        
        st.caption("Note: These are heuristic-based signals for recruiter review only.")

# ============ TAB 7: AI Interview Agent ============
with tab7:
    st.header("AI Interview Agent")

    if not st.session_state.ranked_candidates or not st.session_state.jd_data:
        st.info("Process candidates and a JD to generate interview kits.")
    else:
        ranked = st.session_state.ranked_candidates
        jd = st.session_state.jd_data
        selected_name = st.selectbox("Select candidate", [c["name"] for c in ranked], key="interview_agent_select")
        candidate = next(c for c in ranked if c["name"] == selected_name)
        legacy_gaps = generate_skill_gap_analysis(candidate, jd)
        plan = candidate.get("interview_plan") or generate_interview_plan(candidate, jd, legacy_gaps)

        st.metric("Recommended Round", str(plan.get("recommended_round", "not available")).title())
        st.write("**Focus Areas**")
        focus_areas = plan.get("focus_areas") or []
        if focus_areas:
            for area in focus_areas:
                st.write(f"- {area}")
        else:
            st.info("Focus areas are unavailable for this candidate.")

        st.write("**Interview Questions**")
        questions = plan.get("questions") or []
        if questions:
            for i, item in enumerate(questions, 1):
                st.markdown(f"**Q{i}. [{item.get('type', 'Question')}]** {item.get('question', 'Question unavailable')}")
                st.caption(f"Signal: {item.get('signal', 'Signal unavailable')}")
        else:
            st.info("Interview questions are unavailable for this candidate.")

        st.write("**Scorecard**")
        scorecard = plan.get("scorecard") or []
        if not scorecard and plan.get("scoring_rubric"):
            scorecard = [item.get("criterion", "Review criterion") for item in plan.get("scoring_rubric", [])]
        if scorecard:
            st.write(", ".join(scorecard))
        else:
            st.info("Scorecard is unavailable for this interview plan.")

# ============ TAB 8: Reports, Fairness, Explainable Scoring ============
with tab8:
    st.header("Reports, Fairness, and Explainable Scoring")

    if not st.session_state.ranked_candidates or not st.session_state.jd_data:
        st.info("Process candidates and a JD to generate reports and fairness checks.")
    else:
        ranked = st.session_state.ranked_candidates
        jd = st.session_state.jd_data
        selected_name = st.selectbox("Select candidate", [c["name"] for c in ranked], key="report_candidate_select")
        candidate = next(c for c in ranked if c["name"] == selected_name)

        evidence = candidate.get("score_evidence") or build_score_evidence(candidate, jd)
        gap_report = candidate.get("advanced_skill_gap") or build_advanced_skill_gap(candidate, jd)
        bias_report = candidate.get("bias_report") or analyze_bias_signals(candidate)
        interview_plan = candidate.get("interview_plan") or generate_interview_plan(candidate, jd)

        st.subheader("Explainable Scorecard")
        st.metric("Overall Score", evidence["overall"])
        for dimension in evidence["dimensions"]:
            with st.expander(f"{dimension['dimension']} - {dimension['score']}"):
                st.write(f"Weight: {dimension['weight']}")
                st.write(f"Weighted contribution: {dimension['weighted_contribution']}")
                for item in dimension["evidence"]:
                    st.write(f"- {item}")

        st.subheader("Bias-Aware Screening")
        st.metric("Bias Risk", bias_report["bias_risk_level"])
        if bias_report["signals"]:
            st.dataframe(pd.DataFrame(bias_report["signals"]), use_container_width=True, hide_index=True)
        else:
            st.success("No protected or proxy signals detected in the parsed resume text.")
        with st.expander("Anonymized Screening Profile"):
            st.json(bias_report["anonymized_profile"])
        for guidance in bias_report["fair_screening_guidance"]:
            st.caption(guidance)

        st.subheader("Fairness Ranking Review")
        fairness = build_fairness_dashboard(ranked)
        f1, f2, f3 = st.columns(3)
        f1.metric("Top 3 Skill Overlap", fairness["metrics"]["top3_skill_overlap"])
        f2.metric("Top 3 Education-Blind Overlap", fairness["metrics"]["top3_education_blind_overlap"])
        f3.metric("Bias Signals", fairness["metrics"]["bias_signal_count"])
        st.caption(f"Review status: {fairness['metrics']['review_status']}")

        view_name = st.selectbox(
            "Fairness view",
            ["Skill-only", "Name-blind", "Education-blind"],
            key="fairness_view_select",
        )
        fairness_key = {
            "Skill-only": "skill_only",
            "Name-blind": "name_blind",
            "Education-blind": "education_blind",
        }[view_name]
        st.dataframe(pd.DataFrame(fairness[fairness_key]), use_container_width=True, hide_index=True)
        for guidance in fairness["guidance"]:
            st.caption(guidance)

        st.subheader("Candidate PDF Report")
        if st.button("Generate Candidate PDF Report"):
            try:
                report_path = create_candidate_pdf_report(candidate, jd, evidence, gap_report, interview_plan)
                with open(report_path, "rb") as report_file:
                    st.download_button(
                        "Download PDF Report",
                        report_file.read(),
                        file_name=os.path.basename(report_path),
                        mime="application/pdf",
                    )
                st.success(f"Report generated: {report_path}")
            except RuntimeError as exc:
                st.error(str(exc))

# ============ TAB 9: Batch Analysis and GitHub ============
with tab9:
    st.header("Batch Resume Analysis and GitHub Profile Analyzer")

    if not st.session_state.ranked_candidates:
        st.info("Process candidates to see batch and GitHub analysis.")
    else:
        ranked = st.session_state.ranked_candidates
        summary = build_batch_summary(ranked)

        st.subheader("Batch Health")
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Candidates", summary["total"])
        b2.metric("Strong Hires", summary["strong_hires"])
        b3.metric("Interview Ready", summary["interview_ready"])
        b4.metric("Needs Review", summary["needs_review"])

        st.write("**Top Missing Skills**")
        if summary["top_missing_skills"]:
            st.dataframe(
                pd.DataFrame(summary["top_missing_skills"], columns=["Skill", "Missing Count"]),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success("No recurring missing skills detected.")

        st.subheader("Executive Batch Report")
        if st.button("Generate Executive PDF Report"):
            try:
                report_path = create_executive_pdf_report(st.session_state.jd_data or {}, ranked)
                with open(report_path, "rb") as report_file:
                    st.download_button(
                        "Download Executive PDF",
                        report_file.read(),
                        file_name=os.path.basename(report_path),
                        mime="application/pdf",
                    )
                st.success(f"Executive report generated: {report_path}")
            except RuntimeError as exc:
                st.error(str(exc))

        st.subheader("GitHub Profile Signals")
        github_rows = []
        for candidate in ranked:
            report = candidate.get("github_report") or analyze_github_profile(candidate)
            github_rows.append(
                {
                    "Candidate": candidate.get("name", "Unknown"),
                    "GitHub": report.get("username") or "Not found",
                    "Available": report.get("available"),
                    "Score": report.get("score"),
                    "Summary": report.get("summary"),
                }
            )
        st.dataframe(pd.DataFrame(github_rows), use_container_width=True, hide_index=True)

# Footer
st.divider()
st.caption("AI Recruiter v1.0 • Built with ❤️ using Gemini, FAISS, spaCy, Streamlit • Semantic-first design • For demo & educational use")

# Auto-load samples hint on first run
if not st.session_state.ranked_candidates and not st.session_state.jd_data:
    st.sidebar.info("👈 Click 'Load Sample Dataset' in the sidebar to get started instantly!")
