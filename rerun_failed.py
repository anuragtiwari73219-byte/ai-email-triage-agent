"""
Re-classify only the FAILED rows from eval_results.csv (rate-limit/connection errors),
leaving all successfully-classified rows untouched.
"""

import csv
import time
from dotenv import load_dotenv

load_dotenv()

from ai_agent import EmailTriageAgent

RESULTS_CSV = "eval_results.csv"
SOURCE_CSV = "test_emails.csv"
SLEEP_BETWEEN_CALLS = 3


def main():
    with open(RESULTS_CSV, encoding="utf-8") as f:
        results = list(csv.DictReader(f))

    with open(SOURCE_CSV, encoding="utf-8") as f:
        source = list(csv.DictReader(f))

    if len(results) != len(source):
        print(f"STOP: row count mismatch. results={len(results)} source={len(source)}")
        return

    failed_indices = [
        i for i, r in enumerate(results)
        if str(r.get("model_reason", "")).startswith("Failed:")
    ]

    print(f"Found {len(failed_indices)} failed rows to re-classify.")
    if not failed_indices:
        print("Nothing to do.")
        return

    agent = EmailTriageAgent()
    fixed = 0
    still_failed = 0

    for count, i in enumerate(failed_indices, 1):
        src_row = source[i]
        res_row = results[i]

        src_subj = (src_row.get("subject") or "")[:40]
        res_subj = (res_row.get("subject") or "")[:40]
        if src_subj and res_subj and src_subj[:20] != res_subj[:20]:
            print(f"  [{count}/{len(failed_indices)}] WARNING row {i}: subject mismatch — skipping.")
            continue

        email = {
            "from": src_row.get("from", ""),
            "subject": src_row.get("subject", ""),
            "date": src_row.get("date", ""),
            "body": src_row.get("body", ""),
        }

        print(f"  [{count}/{len(failed_indices)}] Re-classifying: {email['subject'][:50]}")
        result = agent.categorize_email(email)

        reason = result.get("reason", "")
        if str(reason).startswith("Failed:"):
            print(f"    -> still failed: {reason[:100]}")
            still_failed += 1
        else:
            predicted_topic = result.get("topic", "")
            predicted_urgency = result.get("urgency", "")
            expected_topic = res_row.get("expected_topic", "")
            expected_urgency = res_row.get("expected_urgency", "")

            res_row["predicted_topic"] = predicted_topic
            res_row["predicted_urgency"] = predicted_urgency
            res_row["topic_match"] = str(predicted_topic == expected_topic)
            res_row["urgency_match"] = str(predicted_urgency == expected_urgency)
            res_row["both_match"] = str(
                predicted_topic == expected_topic and predicted_urgency == expected_urgency
            )
            res_row["model_reason"] = reason
            fixed += 1
            print(f"    -> fixed: topic={predicted_topic}, urgency={predicted_urgency}")

        time.sleep(SLEEP_BETWEEN_CALLS)

    fieldnames = list(results[0].keys())
    with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nDone. Fixed: {fixed}. Still failed: {still_failed}.")

    total = len(results)
    urgency_correct = sum(1 for r in results if r.get("urgency_match") == "True")
    topic_correct = sum(1 for r in results if r.get("topic_match") == "True")
    both_correct = sum(1 for r in results if r.get("both_match") == "True")
    print(f"\n--- UPDATED SUMMARY ---")
    print(f"Urgency accuracy: {urgency_correct}/{total} ({100*urgency_correct/total:.1f}%)")
    print(f"Topic accuracy:   {topic_correct}/{total} ({100*topic_correct/total:.1f}%)")
    print(f"Both-correct:     {both_correct}/{total} ({100*both_correct/total:.1f}%)")


if __name__ == "__main__":
    main()