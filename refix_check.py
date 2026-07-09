from dotenv import load_dotenv
load_dotenv()

import os
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY_2")

import csv
from ai_agent import EmailTriageAgent

targets = {
    "engineering intern in Remote: 11 new jobs": "job_alert",
    "Lovable AI Developer at Parrot AI Private Limited and 10 more jobs in Remote, India for you. Apply Now.": "job_alert",
    "New Surveys Available for You": "promotional",
    "the intern list you can join before the job posts": "newsletter",
}

agent = EmailTriageAgent()
rows = []
with open('test_emails.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['subject'] in targets:
            rows.append(row)

for row in rows:
    pred = agent.categorize_email({
        "from": row["from"], "subject": row["subject"],
        "date": row["date"], "body": row["body"],
    })
    match = pred.get("topic", "").strip().lower() == row["expected_topic"].strip().lower()
    print(f"{row['subject'][:40]} | expected={row['expected_topic']} | predicted={pred.get('topic')} | match={match} | reason={pred.get('reason','')[:150]}")