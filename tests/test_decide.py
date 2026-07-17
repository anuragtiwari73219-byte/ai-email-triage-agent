from dotenv import load_dotenv
load_dotenv()

from ai_agent import EmailTriageAgent

agent = EmailTriageAgent()

test_emails = [
    {
        "from": "noreply@newsletter.com",
        "subject": "This Week's AI Newsletter Roundup",
        "body": "Here are the top 10 AI news stories this week...",
        "snippet": "Here are the top 10 AI news stories this week...",
    },
    {
        "from": "hr@techcompany.com",
        "subject": "Interview Scheduled - Tomorrow 10 AM",
        "body": "Hi Anurag, your interview is confirmed for tomorrow at 10 AM. Please join the link on time.",
        "snippet": "Hi Anurag, your interview is confirmed for tomorrow at 10 AM.",
    },
    {
        "from": "friend@gmail.com",
        "subject": "Can we catch up this weekend?",
        "body": "Hey, it's been a while. Are you free this weekend to meet up?",
        "snippet": "Hey, it's been a while. Are you free this weekend to meet up?",
    },
    {
        "from": "jobs@internshala.com",
        "subject": "Apply by tonight: AI Engineer Intern role closing soon",
        "body": "A new AI Engineer Internship matching your profile closes applications tonight at 11:59 PM. Apply now before it's gone.",
        "snippet": "AI Engineer Internship closes applications tonight at 11:59 PM.",
    },
    {
        "from": "recruiter@startupxyz.com",
        "subject": "Quick question about your LangChain experience",
        "body": "Hi Anurag, I came across your profile. Do you have hands-on experience with LangGraph in production? Would love to know more before scheduling a call.",
        "snippet": "Do you have hands-on experience with LangGraph in production?",
    },
    {
        "from": "notifications@linkedin.com",
        "subject": "Priya Sharma wants to connect",
        "body": "Priya Sharma has sent you a connection request on LinkedIn.",
        "snippet": "Priya Sharma has sent you a connection request on LinkedIn.",
    },
]

NUM_RUNS = 5
results_by_email = {i: [] for i in range(len(test_emails))}

for run in range(1, NUM_RUNS + 1):
    print(f"\n{'='*20} RUN {run} {'='*20}")
    for i, email in enumerate(test_emails):
        print(f"\n--- Test Email {i+1}: {email['subject']} ---")
        categorization = agent.categorize_email(email)
        print("Categorization:", categorization)
        decision = agent.decide_action(email, categorization)
        print("Decision:", decision)
        results_by_email[i].append(decision['action'])

print(f"\n{'='*20} SUMMARY ({NUM_RUNS} runs) {'='*20}")
for i, email in enumerate(test_emails):
    actions = results_by_email[i]
    consistent = len(set(actions)) == 1
    status = "CONSISTENT" if consistent else "INCONSISTENT"
    print(f"Email {i+1} ({email['subject'][:40]}): {actions} -> {status}")