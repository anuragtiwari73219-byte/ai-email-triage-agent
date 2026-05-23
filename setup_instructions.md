# AI Email Triage Agent — Setup Guide

Complete step-by-step instructions to get the agent running.

---

## Prerequisites

- **Python 3.10+** installed
- **Google account** with Gmail
- **Anthropic API key** with access to `claude-sonnet-4-20250514`

---

## Step 1: Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing one)
3. Navigate to **APIs & Services → Library**
4. Search for **Gmail API** and click **Enable**
5. Go to **APIs & Services → Credentials**
6. Click **+ CREATE CREDENTIALS → OAuth client ID**
7. If prompted, configure the **OAuth consent screen**:
   - Choose **External** user type
   - Fill in app name (e.g., "Email Triage Agent")
   - Add your email as test user
   - Add scope: `https://mail.google.com/`
8. Create **OAuth 2.0 Client ID**:
   - Application type: **Desktop app**
   - Name: "Email Triage Agent"
9. Click **Download JSON** and save as `credentials.json` in the project root folder (`demo02/`)

> ⚠️ **Important**: The `credentials.json` file must be in the same directory as `app.py`.

---

## Step 2: Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/settings/keys)
2. Create a new API key
3. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```
4. Edit `.env` and paste your API key:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

---

## Step 3: Install Dependencies

```bash
cd demo02
pip install -r requirements.txt
```

---

## Step 4: Run the Application

```bash
python app.py
```

This will:
1. Start the Flask server on `http://localhost:5000`
2. Open the web dashboard in your browser

---

## Step 5: First-Time Gmail Authentication

1. Open `http://localhost:5000` in your browser
2. Click **"Connect Gmail"** button
3. A browser window will open for Google OAuth consent
4. Sign in and grant permissions
5. The token will be saved as `token.json` for future sessions

---

## Step 6: Run Triage

1. After connecting Gmail, click **"⚡ Run Triage"**
2. The AI will process your 20 most recent inbox emails
3. Each email will be categorized and drafts will be generated
4. Results appear on the dashboard

---

## Usage

### Dashboard Features
- **Summary Bar**: Shows counts for total emails, urgency levels, drafts, and flagged items
- **Filter Bar**: Filter by urgency, topic, or attention status
- **Email Cards**: Click any card to see full details, AI summary, and draft reply
- **Draft Management**: Generate or regenerate draft replies from the detail modal

### Safety
- ✅ Drafts are saved to Gmail Drafts folder only
- ✅ **No emails are ever auto-sent**
- ✅ High urgency emails are flagged but not auto-replied
- ✅ All drafts require manual review before sending

---

## File Structure

```
demo02/
├── app.py                 # Flask server + API routes
├── gmail_service.py       # Gmail API integration
├── ai_agent.py            # LangChain + Claude AI agent
├── config.py              # Configuration constants
├── requirements.txt       # Python dependencies
├── .env                   # API keys (create from .env.example)
├── .env.example           # Template for .env
├── credentials.json       # Gmail OAuth credentials (you provide)
├── token.json             # Auto-generated after first auth
├── setup_instructions.md  # This file
├── templates/
│   └── dashboard.html     # Web dashboard
└── static/
    ├── css/
    │   └── style.css      # Dashboard styles
    └── js/
        └── app.js         # Frontend logic
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `credentials.json not found` | Download from Google Cloud Console |
| `ANTHROPIC_API_KEY not set` | Check your `.env` file |
| `Token expired` | Delete `token.json` and re-authenticate |
| `Gmail API not enabled` | Enable it in Google Cloud Console |
| `Port 5000 in use` | Change `FLASK_PORT` in `config.py` |
