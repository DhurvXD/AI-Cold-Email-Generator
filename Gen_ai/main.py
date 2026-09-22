import os
from dotenv import load_dotenv

# 1. SETUP: Load environment variables and configure user agent before other imports
load_dotenv()
os.environ.setdefault(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

import streamlit as st
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

# 2. UI CONFIGURATION
st.set_page_config(
    page_title="Cold Email Generator",
    page_icon="📧",
    layout="wide"
)

st.title("📧 AI Cold Email Generator")
st.markdown("Generate tailored, professional cold outreach emails directly from a job posting URL.")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Retrieve API key from environment or Streamlit secrets
    env_api_key = os.getenv("GROQ_API_KEY")
    if not env_api_key and hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
        env_api_key = st.secrets["GROQ_API_KEY"]

    groq_api_key = st.text_input(
        "Groq API Key:",
        value=env_api_key if env_api_key else "",
        type="password",
        help="Loaded automatically from .env or Streamlit secrets if configured."
    )
    
    # Available active models on Groq
    model_choice = st.selectbox(
        "Select Groq Model:",
        options=[
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
            "qwen/qwen3.8-27b"
        ],
        index=0,
        help="openai/gpt-oss-20b is ultra-fast (1,000 tokens/sec) and ideal for email generation."
    )

    sender_name = st.text_input("Your Name:", value="Mohan")
    sender_role = st.text_input("Your Role / Company:", value="Business Development Executive at AtliQ")

# Main Input
default_url = "https://jobs.nike.com"
url_input = st.text_input(
    "Enter a Job Posting URL:",
    value=default_url,
    placeholder="https://example.com/careers/job-role"
)

submit_button = st.button("Generate Cold Email", type="primary")

# 3. PROCESSING LOGIC
if submit_button:
    if not groq_api_key:
        st.error("⚠️ Please provide a Groq API Key in the sidebar or set `GROQ_API_KEY` in your `.env` file.")
    elif not url_input.strip():
        st.warning("⚠️ Please enter a valid job URL.")
    else:
        try:
            with st.spinner("Scraping job details and generating email with Groq..."):
                # Step A: Scrape the website
                loader = WebBaseLoader(url_input.strip())
                docs = loader.load()
                
                if not docs or not docs[0].page_content.strip():
                    st.error("Could not extract text from the provided URL. Please check the link or try another.")
                    st.stop()
                
                # Truncate content reasonably to avoid overflowing token budgets while retaining job info
                page_data = docs[0].page_content.strip()
                if len(page_data) > 15000:
                    page_data = page_data[:15000]

                # Step B: Setup AI with selected valid Groq model
                llm = ChatGroq(
                    temperature=0.2,
                    model_name=model_choice,
                    groq_api_key=groq_api_key
                )

                # Step C: Prompt Template
                prompt_email = PromptTemplate.from_template(
                    """
                    ### JOB DESCRIPTION:
                    {page_data}

                    ### INSTRUCTION:
                    You are {sender_name}, a {sender_role}.
                    Your job is to write a compelling, tailored cold outreach email to the hiring manager or client regarding the job opportunity mentioned above.
                    Highlight how your team's skills, expertise, and solutions can help fulfill their business needs and solve their challenges.
                    Do not provide any preamble, intro remarks, or conversational filler. Output only the email starting with the subject line.

                    ### EMAIL (NO PREAMBLE):
                    """
                )

                # Step D: Run Chain
                chain = prompt_email | llm
                res = chain.invoke({
                    "page_data": page_data,
                    "sender_name": sender_name,
                    "sender_role": sender_role
                })

                email_content = res.content.strip()

            # Step E: Display Result
            st.success("✨ Cold Email Generated Successfully!")
            st.subheader("📬 Generated Cold Email")
            
            # Formatted view
            st.markdown(email_content)
            
            # Copy-friendly text area and download button
            st.divider()
            st.text_area("Raw Text (Easy Copy):", value=email_content, height=280)
            
            st.download_button(
                label="💾 Download Email as Text",
                data=email_content,
                file_name="cold_email.txt",
                mime="text/plain"
            )

        except Exception as e:
            st.error(f"Oops! Something went wrong: {e}")