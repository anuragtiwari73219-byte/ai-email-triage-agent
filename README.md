# 📧 AI Email Triage Agent

An AI agent that automatically categorizes emails by urgency and topic, and drafts replies — powered by Groq (LLaMA 3.3) and LangChain.

## 🔗 Live Demo
👉 [https://ai-email-triage-agent.onrender.com/demo](https://ai-email-triage-agent.onrender.com/demo)

## 💡 Problem It Solves
Inbox overload. This agent reads emails, classifies them as High/Medium/Low urgency, and auto-drafts replies for non-critical ones.

## ⚡ Features
- Auto-categorizes emails by urgency (High / Medium / Low) and topic
- Flags high urgency emails for human attention
- Drafts replies for medium and low urgency emails
- REST API via FastAPI — callable from any frontend

## 🛠 Tech Stack
- Python, FastAPI, LangChain
- Groq API (LLaMA 3.3 70B)
- Deployed on Render

## 🚀 Run Locally
```bash
git clone https://github.com/anuragtiwari73219-byte/ai-email-triage-agent
cd ai-email-triage-agent
pip install -r requirements.txt
# Add GROQ_API_KEY to .env
uvicorn demo_app:app --reload
```