import streamlit as st
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
import os

# 1. SETUP: Tell the app your API Key and "Who" is visiting the website
# Replace 'your_api_key_here' with your actual Groq key
os.environ["GROQ_API_KEY"] = "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"
os.environ["USER_AGENT"] = "MyEmailGeneratorApp"

# 2. UI: These lines show up immediately when you open the browser
st.set_page_config(layout="wide", page_title="Cold Email Generator")
st.title("📧 AI Cold Email Generator")
url_input = st.text_input("Enter a Job URL:", value="https://careers.nike.com/senior-manager-infrastructure-engineering/job/R-82188")
submit_button = st.button("Submit")

# 3. LOGIC: This only happens AFTER you click the button
if submit_button:
    try:
        # Step A: Scrape the website
        loader = WebBaseLoader(url_input)
        page_data = loader.load()[0].page_content
        
        # Step B: Setup the AI (Groq)
        llm = ChatGroq(
            temperature=0,
            model_name="llama-3.1-8b-instant"
        )
        
        # Step C: The Prompt (Instructions for the AI)
        prompt_email = PromptTemplate.from_template(
            """
            ### JOB DESCRIPTION:
            {page_data}
            
            ### INSTRUCTION:
            You are Mohan, a business development executive at AtliQ. 
            Your job is to write a cold email to the client regarding the job mentioned above.
            Do not provide a preamble.
            ### EMAIL (NO PREAMBLE):
            """
        )
        
        # Step D: Run the AI
        chain = prompt_email | llm
        res = chain.invoke({"page_data": page_data})
        
        # Step E: SHOW the result in the UI
        st.subheader("Generated Cold Email:")
        st.code(res.content, language='markdown')
        
    except Exception as e:
        st.error(f"Oops! Something went wrong: {e}")