# AI Cold Email Generator — Vercel Serverless Edition

A single-page, dark-themed, 3D animated web application for generating tailored cold outreach emails directly from career job postings. Powered by Groq's high-speed inference LPUs and deployed entirely on Vercel's serverless infrastructure.

---

## 🚀 Features

- **3D Interactive Dark UI**: Built with Three.js ambient particle dynamics, physical 3D card tilt physics, specular lighting sheen, and responsive mobile-first layout.
- **Vercel Python Serverless Function (`/api/generate`)**:
  - **Passcode Protection**: Guard your Groq token allocation against unauthorized public use via `APP_PASSCODE`.
  - **SSRF Defense**: Strict validation enforcing HTTP/HTTPS schemes, blocking localhost (`127.0.0.1`, `::1`), private RFC1918 subnets, link-local addresses, and cloud metadata endpoints (`169.254.169.254`), with recursive redirect hop inspection.
  - **Zero Bloat**: No heavy LangChain or ChromaDB dependencies; relies solely on ultra-lightweight `requests` and `beautifulsoup4`.
  - **Rate Limiting & Safety**: Built-in sliding-window rate limiting and request payload size caps.
- **One-Click Actions**: Includes inline email previews, instant clipboard copy with visual feedback, and `.txt` file export.

---

## 🛠️ Environment Variables

Configure these in the **Vercel Dashboard** under **Project Settings &rarr; Environment Variables**:

| Variable Name | Required | Description | Example |
| :--- | :--- | :--- | :--- |
| `GROQ_API_KEY` | **Yes** | Your Groq API key from [Groq Console](https://console.groq.com/keys) | `gsk_...` |
| `APP_PASSCODE` | **Yes** | A secret passcode you choose to protect your app | `my_secret_code_123` |

---

## 📦 How to Deploy to Vercel

1. **Import Repository**:
   - Go to [vercel.com/new](https://vercel.com/new) and select your GitHub repository: `AI-Cold-Email-Generator`.
2. **Configure Root Directory**:
   - In the **Root Directory** field, click **Edit** and select **`vercel-app`**.
3. **Add Environment Variables**:
   - Add `GROQ_API_KEY` and `APP_PASSCODE`.
4. **Deploy**:
   - Click **Deploy**. Vercel will build and assign you a live HTTPS domain (e.g., `https://ai-cold-email-generator.vercel.app`).

---

## 🧪 Local Testing

To test the serverless function locally with a Python local server:

```bash
# 1. Set environment variables
export GROQ_API_KEY="your_groq_key"
export APP_PASSCODE="your_passcode"

# 2. Install requirements
pip install -r requirements.txt

# 3. Or use the Vercel CLI
vercel dev
```
