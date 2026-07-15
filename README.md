# 📧 AI Email Triage Agent

An AI agent that automatically categorizes emails by urgency and topic, and drafts replies — powered by Groq (LLaMA 3.3 70B) and LangChain.

## 🎥 Demo Video

Live Gmail connect is disabled on the public web demo for security reasons (see note below). Watch the full working flow here: https://youtu.be/yGKZDPF96Lo

## 💡 Problem It Solves

Inbox overload. This agent reads emails, classifies them as High/Medium/Low urgency and by topic, and auto-drafts replies for non-critical ones.

## ⚡ Features

- Genuinely agentic decision-making — both the categorization step and the action-selection step use LLM-driven tool-calling (Groq/LangChain `bind_tools`), not manual text/JSON parsing
- Auto-categorizes emails by urgency (High / Medium / Low) and topic (9 categories)
- Flags high urgency emails for human attention
- Drafts replies for medium and low urgency emails
- Deterministic guardrail on top of the LLM's action choice: emails classified as Personal, Networking, or Application_Status that are flagged as needing human attention are never silently archived, regardless of what the model's tool call says — this closes a measured ~40% inconsistency gap in the model's own tool selection on ambiguous emails
- REST API via Flask — callable from any frontend

## 📊 Evaluation

Evaluated on a 93-email manually labeled dev set (used during prompt tuning):
- Topic classification accuracy: 93.5% (87/93)
- Urgency classification accuracy: 96.8% (90/93)
- Both correct: 91.4% (85/93)

Also validated on a separate 30-email holdout set (not used in prompt tuning):
- Topic classification accuracy: 90% (27/30)
- Urgency classification accuracy: 100% (30/30)
- Both correct: 90% (27/30)

Eval scripts (`eval_triage.py`, `eval_holdout.py`) and labeled data (`test_emails.csv`, `eval_results.csv`, `test_emails_holdout.csv`, `eval_results_holdout.csv`) are included in this repo for reproducibility.

## 🛠 Tech Stack

- Python, Flask, LangChain
- Groq API (LLaMA 3.3 70B)
- Deployed on Render

## 🚀 Run Locally

```bash
git clone https://github.com/anuragtiwari73219-byte/ai-email-triage-agent
cd ai-email-triage-agent
pip install -r requirements.txt
# Add GROQ_API_KEY and GITHUB credentials to .env
python app.py
```