from dotenv import load_dotenv
load_dotenv()

from ai_agent import EmailTriageAgent

agent = EmailTriageAgent()

test_email = {
    "from": "recruiter@company.com",
    "subject": "Quick question about your LangChain experience",
    "date": "2026-07-15",
    "body": "Hi, I saw your project and wanted to ask about your experience with LangChain. Are you available for a quick call this week?",
}

categorization = agent.categorize_email(test_email)
decision = agent.decide_action(test_email, categorization)

print("Topic:", categorization.get('topic'))
print("Needs attention:", categorization.get('needs_human_attention'))
print("Final action:", decision['action'])
print("Reasoning:", decision['reasoning'])
