import csv
from gmail_service import GmailService

gmail = GmailService()
gmail.authenticate()

emails = gmail.get_emails(max_results=100)

with open("test_emails_100.csv", "w", newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=["from", "subject", "date", "body", "expected_urgency", "expected_topic"])
    writer.writeheader()
    for e in emails:
        writer.writerow({
            "from": e.get("from", ""),
            "subject": e.get("subject", ""),
            "date": e.get("date", ""),
            "body": (e.get("body") or e.get("snippet", ""))[:500],
            "expected_urgency": "",
            "expected_topic": "",
        })