#!/usr/bin/env python3
"""
Generate sample resume and JD PDFs for AI Recruiter demo.
"""
from fpdf import FPDF
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
RESUMES_DIR = os.path.join(DATA_DIR, "resumes")
JD_DIR = os.path.join(DATA_DIR, "jd")

os.makedirs(RESUMES_DIR, exist_ok=True)
os.makedirs(JD_DIR, exist_ok=True)

def create_pdf(text, filename, title="Document"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    pdf.set_font("Helvetica", size=10)
    
    # Title
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)
    
    pdf.set_font("Helvetica", size=10)
    for line in text.split("\n"):
        if line.strip():
            # Handle long lines - use multi_cell with explicit width
            effective_width = 180  # approx safe width in mm
            pdf.multi_cell(effective_width, 5, line)
        else:
            pdf.ln(2)
    pdf.output(filename)
    print(f"Created: {filename}")

# Sample Job Description
jd_text = """Job Title: Senior Machine Learning Engineer

Company: TechNova AI

Location: Remote / Bangalore, India

Experience Required: 3+ years in Machine Learning / Data Science

Education: Bachelor's or Master's in Computer Science, Data Science, or related field

Required Skills:
- Strong proficiency in Python
- Experience with TensorFlow or PyTorch
- AWS (SageMaker, EC2, S3, Lambda)
- Machine Learning algorithms and model deployment
- NLP and LLM experience preferred
- SQL and data pipelines

Preferred Skills:
- Experience with Docker and Kubernetes
- MLOps practices (MLflow, Kubeflow)
- Computer Vision
- Big data tools (Spark, Hadoop)
- Publications or open source contributions

Responsibilities:
- Design, develop and deploy ML models for production
- Build scalable data pipelines
- Collaborate with product and engineering teams
- Mentor junior engineers
- Stay up to date with latest AI research

Key Projects Expected:
- End-to-end ML systems
- NLP applications (chatbots, summarization)
- Recommendation systems or fraud detection

"""

create_pdf(jd_text, os.path.join(JD_DIR, "ml_engineer_jd.pdf"), "Job Description - Senior ML Engineer")

# Sample Resume 1: Strong match - John Doe
resume1 = """JOHN DOE
Email: john.doe@email.com | Phone: +91-9876543210 | LinkedIn: linkedin.com/in/johndoe | Location: Bangalore, India

PROFESSIONAL SUMMARY
Senior Machine Learning Engineer with 4+ years of experience building and deploying production ML systems. Expertise in Python, TensorFlow, PyTorch, and AWS. Passionate about NLP and LLMs.

SKILLS
Programming: Python, SQL, Java
Machine Learning: TensorFlow, PyTorch, Scikit-learn, XGBoost, Hugging Face
Cloud & MLOps: AWS (SageMaker, Lambda, S3, EC2), Docker, Kubernetes, MLflow
Data: Pandas, NumPy, Spark, SQL
NLP/LLM: Transformers, LangChain, OpenAI APIs, RAG systems
Other: Git, CI/CD, FastAPI

EXPERIENCE
Senior ML Engineer | TechCorp AI | Bangalore | Jan 2022 - Present
- Led development of NLP-based document processing system using BERT and LLMs, improving accuracy by 35%
- Built and deployed recommendation engine on AWS SageMaker serving 1M+ users
- Implemented MLOps pipelines with MLflow and Kubernetes reducing deployment time by 60%
- Mentored 3 junior engineers on ML best practices

ML Engineer | DataSense | Bangalore | Jun 2020 - Dec 2021
- Developed fraud detection model using XGBoost and deep learning achieving 98% precision
- Created data pipelines with Apache Spark and AWS Glue
- Deployed models as REST APIs using FastAPI and Docker

EDUCATION
M.Tech in Computer Science (AI Specialization) | IIT Delhi | 2018 - 2020 | CGPA: 9.2
B.Tech in Computer Science | NIT Karnataka | 2014 - 2018 | CGPA: 8.7

PROJECTS
- LLM-Powered Resume Screening Tool: Built end-to-end RAG system using LangChain, Pinecone, and Gemini. Reduced manual screening time by 80%.
- Brain Tumor Detection from MRI: Computer vision model using PyTorch and ResNet, deployed on AWS. Achieved 96% accuracy.
- Real-time Sentiment Analysis API: NLP pipeline with BERT, deployed on AWS Lambda.

CERTIFICATIONS
- AWS Certified Machine Learning - Specialty
- Google Professional ML Engineer
"""

create_pdf(resume1, os.path.join(RESUMES_DIR, "john_doe_strong_match.pdf"), "Resume - John Doe")

# Sample Resume 2: Medium match - Jane Smith
resume2 = """JANE SMITH
Email: jane.smith@email.com | Phone: +91-9123456780 | LinkedIn: linkedin.com/in/janesmith | Location: Hyderabad, India

PROFESSIONAL SUMMARY
Data Scientist with 2.5 years experience in ML and analytics. Strong Python and data skills. Some exposure to TensorFlow and AWS. Eager to grow in production ML systems.

SKILLS
Programming: Python, R, SQL, JavaScript
Machine Learning: Scikit-learn, TensorFlow (basic), XGBoost, LightGBM
Cloud: AWS (basic EC2, S3), GCP
Data: Pandas, NumPy, SQL, Matplotlib, Seaborn
NLP: NLTK, basic spaCy, simple sentiment models
Tools: Git, Jupyter, Tableau

EXPERIENCE
Data Scientist | AnalyticsHub | Hyderabad | Mar 2022 - Present
- Built customer churn prediction model using XGBoost and Scikit-learn (92% accuracy)
- Developed interactive dashboards in Tableau and Streamlit for business stakeholders
- Created ETL pipelines using Python and AWS Glue (limited)
- Analyzed large datasets using SQL and Pandas

Junior Data Analyst | FinTech Solutions | Hyderabad | Jul 2021 - Feb 2022
- Performed exploratory data analysis and statistical modeling
- Automated reporting using Python scripts
- Supported A/B testing for product features

EDUCATION
M.Sc. in Data Science | University of Hyderabad | 2019 - 2021 | CGPA: 8.5
B.Sc. in Statistics | Osmania University | 2016 - 2019 | CGPA: 8.0

PROJECTS
- Customer Segmentation using K-Means and PCA: Deployed as Streamlit app.
- Sentiment Analysis on Twitter Data: Used NLTK and basic deep learning.
- Sales Forecasting with Time Series: ARIMA and Prophet models.

CERTIFICATIONS
- Google Data Analytics Professional Certificate
"""

create_pdf(resume2, os.path.join(RESUMES_DIR, "jane_smith_medium.pdf"), "Resume - Jane Smith")

# Sample Resume 3: Weaker match - Bob Johnson
resume3 = """BOB JOHNSON
Email: bob.johnson@email.com | Phone: +91-9988776655 | LinkedIn: linkedin.com/in/bobjohnson | Location: Pune, India

PROFESSIONAL SUMMARY
Software Engineer with 3 years experience in web development and backend systems. Some Python scripting. Interested in transitioning to AI/ML roles. Strong in Java and cloud basics.

SKILLS
Programming: Java, Python (intermediate), JavaScript, SQL, C++
Web/Backend: Spring Boot, React, Node.js, PostgreSQL
Cloud: Azure (basic), Docker
Data: Basic Pandas, Excel, SQL queries
Other: Git, Jenkins, REST APIs

EXPERIENCE
Software Engineer | WebScale Inc | Pune | Aug 2021 - Present
- Developed microservices using Java Spring Boot and React frontend
- Built REST APIs and integrated with PostgreSQL
- Containerized applications with Docker
- Implemented CI/CD pipelines with Jenkins

Software Developer Intern | StartupXYZ | Pune | Jan 2021 - Jul 2021
- Worked on Python scripts for data processing
- Maintained legacy Java applications

EDUCATION
B.Tech in Computer Engineering | VIT Pune | 2017 - 2021 | CGPA: 7.8

PROJECTS
- E-commerce Platform: Full stack app with Java backend and React.
- Task Management API: RESTful service with authentication.
- Basic Data Dashboard: Python + Pandas + Matplotlib for internal sales data.

CERTIFICATIONS
- Microsoft Azure Fundamentals (AZ-900)
"""

create_pdf(resume3, os.path.join(RESUMES_DIR, "bob_johnson_weaker.pdf"), "Resume - Bob Johnson")

# Sample Resume 4: Good match with NLP focus - Alice Chen
resume4 = """ALICE CHEN
Email: alice.chen@email.com | Phone: +91-8877665544 | LinkedIn: linkedin.com/in/alicechen | Location: Bangalore, India

PROFESSIONAL SUMMARY
ML Engineer specializing in NLP and LLMs with 3 years experience. Expert in Python, Hugging Face, and building RAG systems. Experience with AWS and TensorFlow.

SKILLS
Programming: Python, SQL, TypeScript
Machine Learning: TensorFlow, PyTorch, Hugging Face Transformers, LangChain, LlamaIndex
NLP/LLM: BERT, GPT fine-tuning, RAG, Vector DBs (Pinecone, Weaviate), Prompt Engineering
Cloud: AWS (SageMaker, Bedrock, Lambda, S3), GCP Vertex AI
MLOps: Docker, Kubernetes, FastAPI, MLflow
Data Science: Pandas, NumPy, Scikit-learn, SQL

EXPERIENCE
ML Engineer - NLP | AILabs | Bangalore | Feb 2022 - Present
- Designed and deployed multiple LLM-powered applications including chatbot and document Q&A using LangChain + RAG achieving 85% user satisfaction
- Fine-tuned BERT models for domain-specific NER and classification tasks
- Built scalable inference pipelines on AWS SageMaker and integrated with production apps
- Led initiative to evaluate and integrate open-source LLMs (Llama, Mistral)

AI Research Engineer | ResearchCo | Bangalore | Jun 2021 - Jan 2022
- Worked on research projects in NLP and information retrieval
- Published paper on efficient transformer inference
- Implemented data pipelines and model training infrastructure

EDUCATION
M.S. in Artificial Intelligence | Stanford University (online) | 2020 - 2022
B.Tech in Computer Science | BITS Pilani | 2016 - 2020 | CGPA: 9.0

PROJECTS
- Enterprise RAG System: Full production RAG with hybrid search, citation, and evaluation framework. Used by 500+ employees.
- Multi-lingual Chatbot: Fine-tuned models for 5 Indian languages.
- Automated Resume Parser: Used NER + LLMs to extract structured data from PDFs (similar to this system!)

CERTIFICATIONS
- AWS Certified AI Practitioner
- DeepLearning.AI LLM Engineering
"""

create_pdf(resume4, os.path.join(RESUMES_DIR, "alice_chen_nlp.pdf"), "Resume - Alice Chen")

print("\n✅ All sample PDFs generated successfully in data/resumes/ and data/jd/")
print("Files created:")
for root, dirs, files in os.walk(DATA_DIR):
    for f in files:
        print(f"  {os.path.join(root, f)}")
