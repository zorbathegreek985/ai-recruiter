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
from parsers.resume_parser import batch_parse_resumes, extract_structured_resume
from parsers.jd_parser import extract_structured_jd
from ranking.ranking_engine import rank_candidates, compute_overall_score
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
from embeddings.embedding_engine import semantic_similarity

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
    .main-header {font-size: 2.5rem; font-weight: 700; color: #1a73e8;}
    .score-badge {padding: 4px 12px; border-radius: 20px; font-weight: 600;}
    .high-score {background-color: #d4edda; color: #155724;}
    .medium-score {background-color: #fff3cd; color: #856404;}
    .low-score {background-color: #f8d7da; color: #721c24;}
    .stTabs [data-baseweb="tab-list"] {gap: 8px;}
    .candidate-card {border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px; margin: 8px 0;}
</style>
""", unsafe_allow_html=True)

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

def load_samples():
    """Load the pre-generated sample data (prefers clean .txt for reliable demo parsing)."""
    jd_path = "data/jd/ml_engineer_jd.txt"  # reliable text
    resume_paths = [
        "data/resumes/john_doe_strong_match.txt",
        "data/resumes/alice_chen_nlp.txt",
        "data/resumes/jane_smith_medium.txt",
        "data/resumes/bob_johnson_weaker.txt"
    ]
    
    with st.spinner("Loading and parsing sample data..."):
        # Parse JD
        jd = extract_structured_jd(jd_path)
        st.session_state.jd_data = jd
        
        # Parse resumes (txt supported)
        parsed = batch_parse_resumes(resume_paths)
        st.session_state.candidates = parsed
        
        # Rank
        ranked = rank_candidates(parsed, jd)
        st.session_state.ranked_candidates = ranked
        
        # Rebuild vector store
        vector_store.candidates = []
        vector_store.embeddings = []
        vector_store.add_candidates(parsed)
        st.session_state.vector_store_loaded = True
        
    st.success("✅ Sample data loaded! Explore the tabs below.")
    st.rerun()

# Main Header
st.markdown('<h1 class="main-header">🤖 AI Recruiter</h1>', unsafe_allow_html=True)
st.caption("Intelligent Candidate Discovery & Ranking using Semantic AI • Explainable • Production Ready")

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📄 Job Description", 
    "📁 Resumes & Ranking", 
    "🔍 Recruiter Search (RAG)", 
    "📊 Analytics", 
    "🔎 Skill Gaps & Insights",
    "💬 AI Chatbot & Tools"
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
                        jd = extract_structured_jd(tmp_path)
                    else:
                        jd = extract_structured_jd(jd_text_input or jd_file.getvalue().decode())
                    os.unlink(tmp_path)
                elif jd_text_input.strip():
                    jd = extract_structured_jd(jd_text_input)
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
        "Upload multiple PDF resumes (max 20)",
        type=["pdf"],
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
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
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
                        ranked = rank_candidates(parsed_cands, st.session_state.jd_data)
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
        
        # KPI cards
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total Candidates", stats["total"])
        kpi2.metric("Avg Match Score", f"{stats['avg_score']}%")
        kpi3.metric("Top Score", f"{stats['top_score']}%")
        kpi4.metric("High Match (≥80%)", stats["high_match"])
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(
                create_ranking_distribution_chart(ranked),
                use_container_width=True
            )
            st.plotly_chart(
                create_average_match_gauge(ranked),
                use_container_width=True
            )
        
        with col2:
            st.plotly_chart(
                create_top_skills_chart(ranked),
                use_container_width=True
            )
            if jd:
                st.plotly_chart(
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
            st.plotly_chart(create_score_breakdown_chart(selected_cand), use_container_width=True)

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
            
            names = {}
            emails = {}
            
            for i, c1 in enumerate(ranked):
                name = c1.get("name", "").lower()
                email = c1.get("email", "").lower() if c1.get("email") else None
                
                # Duplicate by name/email
                if name in names:
                    duplicate_pairs.append((names[name], c1["name"]))
                else:
                    names[name] = c1["name"]
                if email and email in emails:
                    duplicate_pairs.append((emails[email], c1["name"]))
                elif email:
                    emails[email] = c1["name"]
                
                # Simple fraud heuristics
                text = c1.get("raw_text", "").lower()
                fraud_score = 0
                reasons = []
                
                # Keyword stuffing
                if text.count("python") > 8 or text.count("tensorflow") > 5:
                    fraud_score += 30
                    reasons.append("High repetition of keywords (possible stuffing)")
                
                # Very short resume
                if len(text) < 800:
                    fraud_score += 25
                    reasons.append("Unusually short resume content")
                
                # Mismatch: claims high exp but few projects/skills
                if c1.get("experience_years", 0) > 5 and len(c1.get("skills", [])) < 4:
                    fraud_score += 20
                    reasons.append("High experience claimed with very few skills listed")
                
                if fraud_score > 25:
                    fraud_reports.append({
                        "name": c1["name"],
                        "score": fraud_score,
                        "reasons": reasons
                    })
            
            if duplicate_pairs:
                st.warning("**Possible Duplicates Found:**")
                for p in set(duplicate_pairs):
                    st.write(f"- {p[0]} and {p[1]}")
            else:
                st.success("No obvious duplicates detected.")
            
            if fraud_reports:
                st.error("**Potential Fraud / Low-Quality Resumes:**")
                for f in fraud_reports:
                    st.write(f"• **{f['name']}** (Risk: {f['score']}) — {', '.join(f['reasons'])}")
            else:
                st.success("No obvious fraud signals detected in current batch.")
        
        st.caption("Note: These are heuristic-based signals for recruiter review only.")

# Footer
st.divider()
st.caption("AI Recruiter v1.0 • Built with ❤️ using Gemini, FAISS, spaCy, Streamlit • Semantic-first design • For demo & educational use")

# Auto-load samples hint on first run
if not st.session_state.ranked_candidates and not st.session_state.jd_data:
    st.sidebar.info("👈 Click 'Load Sample Dataset' in the sidebar to get started instantly!")
