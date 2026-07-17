from dotenv import load_dotenv
load_dotenv()

from ai_agent import EmailTriageAgent

agent = EmailTriageAgent()

test_emails = [
    {
        "id": "test1",
        "from": "noreply@newsletter.com",
        "subject": "This Week's AI Newsletter Roundup",
        "body": "Here are the top 10 AI news stories this week...",
        "snippet": "Here are the top 10 AI news stories this week...",
    },
    {
        "id": "test2",
        "from": "hr@techcompany.com",
        "subject": "Interview Scheduled - Tomorrow 10 AM",
        "body": "Hi Anurag, your interview is confirmed for tomorrow at 10 AM.",
        "snippet": "Hi Anurag, your interview is confirmed for tomorrow at 10 AM.",
    },
    {
        "id": "test3",
        "from": "friend@gmail.com",
        "subject": "Can we catch up this weekend?",
        "body": "Hey, it's been a while. Are you free this weekend?",
        "snippet": "Hey, it's been a while. Are you free this weekend?",
    },
]

results = agent.triage_inbox(test_emails)

for r in results:
    print(f"\nSubject: {r['subject']}")
    print(f"  urgency={r['urgency']}, topic={r['topic']}")
    print(f"  agent_action={r['agent_action']}")
    print(f"  needs_human_attention={r['needs_human_attention']}")
    print(f"  draft_reply={r['draft_reply']}")