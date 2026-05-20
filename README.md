<img width="1910" height="1031" alt="AI-Cold-Email-Generator" src="https://github.com/user-attachments/assets/a51d22bf-c158-4367-85e9-ba3b47cf18cc" />






📧 Cold Email Generator Using Llama 3.1 & LangChain
     
🚀 Project Overview:

This project is an end-to-end GenAI application designed to help Business Development Executives (BDEs) and sales teams at software service companies automate their client acquisition process.
When service companies discover a potential client (e.g., Nike) hiring for software engineers on a job portal, they can pitch their own contract-based developers to save the client time and money. Writing these personalized cold emails manually for every job posting is incredibly time-consuming.
This tool solves that problem by automatically scraping the job description from a URL, extracting the required technical skills, matching those skills with the service company's internal portfolio, and generating a highly tailored cold email. This is based on real-world techniques used by actual software consulting companies.

✨ Key Features:

Automated Web Scraping: Extracts raw text and HTML from any active job posting URL using LangChain's WebBaseLoader.
Intelligent Data Extraction: Uses Llama 3.1 to filter out webpage clutter (like navigation buttons) and securely extract the exact Job Role, Experience, and Core Skills in a clean JSON format using a strict "No Preamble" prompt.
Semantic Portfolio Matching: Replaces traditional keyword-based databases with ChromaDB (a Vector Database). If a job needs specific skills, the database uses semantic search to automatically fetch the company's relevant tech portfolio links by measuring Euclidean distance.
Lightning-Fast Generation: Instead of running the LLM locally (which can take up to 5 minutes per query), this project uses the Groq API. Groq utilizes LPUs (Language Processing Units) to deliver near-instantaneous LLM inference.
Interactive UI: A clean, user-friendly frontend built rapidly with Streamlit.

🛠️ Tech Stack:

Large Language Model: Meta Llama 3.1 (70B parameters)
Cloud Inference: Groq Cloud API
Orchestration Framework: LangChain
Vector Database: ChromaDB (Open-source & lightweight)
Frontend UI: Streamlit
Data Handling: Pandas (for processing portfolio CSVs)

🧠 Application Architecture & Workflow:

Input: The user pastes a job URL into the Streamlit interface.
Scraping & Cleaning: LangChain scrapes the page, and a custom clean_text utility removes redundant HTTP tags, special characters, and garbage data.
Information Extraction: The clean text is passed to Llama 3.1 with a strict "No Preamble" prompt. This forces the LLM to skip conversational text and output only a parsed JSON dictionary containing the job skills using a JsonOutputParser.
Semantic Search: The extracted skills are queried against ChromaDB (which holds the company's tech stack and project links). ChromaDB finds the closest matching portfolio links.
Email Generation: The job description and the matching portfolio links are injected into a final Prompt Template, instructing the LLM to act as a BDE and write a compelling cold email.

Project Structure:

<img width="1472" height="1040" alt="image" src="https://github.com/user-attachments/assets/ef922160-1bb3-41b7-9748-2600f71ff7a3" />

⚙️ Installation & Setup Guide:

1. Clone the repository:
git clone https://github.com/YourUsername/cold-email-generator.git
cd cold-email-generator
2. Install dependencies: Make sure you have Python installed, then run:
pip install -r requirements.txt
3. Get your Groq API Key:
Go to console.groq.com and log in.
Navigate to the API Keys section and generate a new key.
4. Set up Environment Variables:
In the root folder, create a file exactly named .env.
Add your API key to this file like so:
GROQ_API_KEY="paste_your_api_key_here"
Security Note: Never commit your .env file to GitHub.
5. Run the Application: Execute the Streamlit app from your terminal:
streamlit run app/main.py


