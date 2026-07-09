"""
Eval script for EmailTriageAgent.categorize_email()

How to use:
1. Put this file in the SAME folder as ai_agent.py (clone your repo, drop this in).
2. Fill in test_emails.csv with 20 rows: from, subject, date, body, expected_urgency, expected_topic
   - expected_urgency must be one of: High, Medium, Low
   - expected_topic must be one of: Work, Finance, Promotions, Personal, Spam
3. Make sure GROQ_API_KEY is set in your environment (or .env loaded).
4. Run: python eval_triage.py
5. Output: eval_results.csv with predictions + a printed accuracy summary.

This tests against the REAL schema your code returns (urgency + topic),
not "Urgent/Followup/Spam/Info" — that labeling doesn't exist in ai_agent.py.
"""

import csv
import time
from dotenv import load_dotenv
load_dotenv()
from ai_agent import EmailTriageAgent

INPUT_CSV = "test_emails.csv"
OUTPUT_CSV = "eval_results.csv"

def load_test_set(path):
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def run_eval():
    agent = EmailTriageAgent()
    rows = load_test_set(INPUT_CSV)

    results = []
    urgency_correct = 0
    topic_correct = 0
    both_correct = 0

    for i, row in enumerate(rows):
        email = {
            "from": row.get("from", ""),
            "subject": row.get("subject", ""),
            "date": row.get("date", ""),
            "body": row.get("body", ""),
        }
        print(f"[{i+1}/{len(rows)}] Classifying: {email['subject'][:50]}")

        prediction = agent.categorize_email(email)

        pred_urgency = prediction.get("urgency", "")
        pred_topic = prediction.get("topic", "")
        exp_urgency = row.get("expected_urgency", "").strip()
        exp_topic = row.get("expected_topic", "").strip()

        u_match = pred_urgency.strip().lower() == exp_urgency.lower()
        t_match = pred_topic.strip().lower() == exp_topic.lower()

        if u_match:
            urgency_correct += 1
        if t_match:
            topic_correct += 1
        if u_match and t_match:
            both_correct += 1

        results.append({
            "subject": email["subject"],
            "expected_urgency": exp_urgency,
            "predicted_urgency": pred_urgency,
            "urgency_match": u_match,
            "expected_topic": exp_topic,
            "predicted_topic": pred_topic,
            "topic_match": t_match,
            "both_match": u_match and t_match,
            "model_reason": prediction.get("reason", ""),
        })

        time.sleep(1)  # gentle on rate limits

    with open(OUTPUT_CSV, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    n = len(rows)
    print("\n--- EVAL SUMMARY ---")
    print(f"Total emails tested: {n}")
    print(f"Urgency accuracy: {urgency_correct}/{n} ({100*urgency_correct/n:.1f}%)")
    print(f"Topic accuracy:   {topic_correct}/{n} ({100*topic_correct/n:.1f}%)")
    print(f"Both-correct (strict): {both_correct}/{n} ({100*both_correct/n:.1f}%)")
    print(f"\nFull results saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    run_eval()