# 📧 AI Email Triage Agent
An AI agent that automatically categorizes emails by urgency and topic, and drafts replies — powered by Groq (LLaMA 3.3 70B) and LangChain.

## 🔗 Live Demo
👉 [https://ai-email-triage-agent.onrender.com/demo](https://ai-email-triage-agent.onrender.com/demo)

## 💡 Problem It Solves
Inbox overload. This agent reads emails, classifies them as High/Medium/Low urgency and by topic, and auto-drafts replies for non-critical ones.

## ⚡ Features
- Auto-categorizes emails by urgency (High / Medium / Low) and topic (9 categories)
- Flags high urgency emails for human attention
- Drafts replies for medium and low urgency emails
- REST API via FastAPI — callable from any frontend

## 📊 Evaluation
Evaluated on a 93-email manually labeled dev set (7 emails excluded due to API rate limiting during eval run):
- Topic classification accuracy: 93.5% (87/93)
- Urgency classification accuracy: 96.8% (90/93)
- Both correct: 91.4% (85/93)

Note: this is a dev set used during prompt tuning, not a held-out test set. Eval scripts (`eval_triage.py`, `check_clean.py`, `patch_results.py`) and labeled data (`test_emails.csv`, `eval_results.csv`) are included in this repo for reproducibility.

## 🛠 Tech Stack
- Python, FastAPI, LangChain
- Groq API (LLaMA 3.3 70B)
- Deployed on Render

## 🚀 Run Locally
```bash
git clone https://github.com/anuragtiwari73219-byte/ai-email-triage-agent
cd ai-email-triage-agent
pip install -r requirements.txt
# Add GROQ_API_KEY and GITHUB credentials to .env
uvicorn app:app --reload
```