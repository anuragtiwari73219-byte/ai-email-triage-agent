from fastapi import FastAPI
from ai_agent import EmailTriageAgent
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()
agent = EmailTriageAgent()

SAMPLE_EMAILS = [
    {
        "from": "boss@company.com",
        "subject": "URGENT: Server is down",
        "date": "2024-01-15",
        "body": "Our production server crashed. Customers cannot access the service. Fix immediately."
    },
    {
        "from": "newsletter@medium.com", 
        "subject": "Your weekly digest",
        "date": "2024-01-15",
        "body": "Here are the top 10 articles this week in AI and technology."
    },
    {
        "from": "hr@company.com",
        "subject": "Meeting tomorrow at 3pm",
        "date": "2024-01-15",
        "body": "Please confirm your attendance for the quarterly review meeting tomorrow."
    }
]

@app.get("/")
def home():
    return {"message": "Email Triage Agent is running"}

@app.get("/demo")
def demo():
    results = agent.triage_inbox(SAMPLE_EMAILS)
    return {"triaged_emails": results}