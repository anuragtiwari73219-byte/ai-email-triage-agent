import csv

fixes = {
    "engineering intern in Remote: 11 new jobs": "job_alert",
    "Lovable AI Developer at Parrot AI Private Limited and 10 more jobs in Remote, India for you. Apply Now.": "job_alert",
    "New Surveys Available for You": "promotional",
    "the intern list you can join before the job posts": "newsletter",
}

rows = []
with open('test_emails.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for row in reader:
        subj = row['subject']
        if subj in fixes:
            print(f"Fixing: {subj[:50]} -> {fixes[subj]}")
            row['expected_topic'] = fixes[subj]
        rows.append(row)

with open('test_emails.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("Done.")