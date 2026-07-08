import json
import time
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq


class EmailTriageAgent:

    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            self._llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                groq_api_key=os.getenv("GROQ_API_KEY"),
                temperature=0,
            )
        return self._llm

    def categorize_email(self, email):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert AI email triage assistant. Analyze the given email and categorize it.

Urgency levels (use these exact definitions):
- "High": requires action within hours; explicit deadline today/tomorrow, or blocks someone else's work right now.
- "Medium": requires a response or action within a few days; no immediate deadline, but ignoring it has a real consequence (e.g. a social commitment, a routine bill, a job-application follow-up).
- "Low": no response needed, or purely informational (promotions, automated notifications, receipts).

Topic categories (use these exact definitions):
- "Job_Alert": automated job listing notifications (LinkedIn, Indeed, Naukri, Glassdoor, Internshala, Jobright, etc.)
- "Application_Status": updates on an application you submitted (confirmation, status change, interview invite)
- "Networking": LinkedIn connection requests, messages, "X wants to connect", profile views
- "Newsletter": recurring digest/newsletter content (industry news, curated roundups)
- "Promotional": marketing, discounts, product promotions, upsell nudges
- "Finance": bank statements, bills, payment receipts, financial notifications
- "Spam": unsolicited, irrelevant, or clearly junk mail
- "Personal": genuine personal correspondence from real contacts
- "Other": anything that doesn't fit the above

Examples:
- "Can we get on a call this week?" -> Medium urgency
- "Server down, need fix now" -> High urgency
- "Your order has shipped" -> Low urgency
- "New job posting notification from LinkedIn/Indeed" -> Job_Alert
- "Your application status update" -> Application_Status
- "X wants to connect on LinkedIn" -> Networking
- "Weekly newsletter/digest content" -> Newsletter

Return your response as a valid JSON object with exactly these fields:
- "urgency": one of "High", "Medium", "Low"
- "topic": one of "Job_Alert", "Application_Status", "Networking", "Newsletter", "Promotional", "Finance", "Spam", "Personal", "Other"
- "summary": a concise 1-2 sentence summary
- "needs_human_attention": boolean
- "reason": brief explanation

Return ONLY the JSON object."""),
            ("human", "From: {sender}\nSubject: {subject}\nDate: {date}\n\nBody:\n{body}"),
        ])

        chain = prompt | self.llm
        last_error = None

        for attempt in range(4):
            try:
                response = chain.invoke({
                    "sender": email.get('from', 'Unknown'),
                    "subject": email.get('subject', '(No Subject)'),
                    "date": email.get('date', ''),
                    "body": (email.get('body') or email.get('snippet', ''))[:3000],
                })
                content = response.content.strip()
                if content.startswith('```'):
                    content = content.split('\n', 1)[1].rsplit('```', 1)[0].strip()
                if content.startswith('{'):
                    result = json.loads(content)
                else:
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    result = json.loads(content[start:end])
                result.setdefault('urgency', 'Medium')
                result.setdefault('topic', 'Other')
                result.setdefault('summary', '')
                result.setdefault('needs_human_attention', True)
                result.setdefault('reason', '')
                return result
            except Exception as e:
                last_error = e
                if '429' in str(e) or 'quota' in str(e).lower():
                    time.sleep(5 * (2 ** attempt))
                else:
                    break

        return {
            "urgency": "Medium",
            "topic": "Other",
            "summary": "",
            "needs_human_attention": True,
            "reason": f"Failed: {str(last_error)}",
        }

    def draft_reply(self, email):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional email assistant. Write a concise reply under 150 words. Always sign the reply as "Anurag Tiwari" â€” never use a placeholder like "[Your Name]". Return ONLY the reply text."""),
            ("human", "From: {sender}\nSubject: {subject}\n\nBody:\n{body}"),
        ])
        chain = prompt | self.llm
        for attempt in range(4):
            try:
                response = chain.invoke({
                    "sender": email.get('from', 'Unknown'),
                    "subject": email.get('subject', ''),
                    "body": (email.get('body') or email.get('snippet', ''))[:3000],
                })
                return response.content.strip()
            except Exception as e:
                if '429' in str(e) or 'quota' in str(e).lower():
                    time.sleep(5 * (2 ** attempt))
                else:
                    break
        return f"Thank you for your email regarding \"{email.get('subject', '')}\"."

    def triage_inbox(self, emails, gmail_service=None):
        triaged = []
        for i, email in enumerate(emails):
            print(f"[Triage] {i+1}/{len(emails)}: {email.get('subject', '?')[:50]}")
            categorization = self.categorize_email(email)
            email_result = {
                **email,
                'urgency': categorization.get('urgency', 'Medium'),
                'topic': categorization.get('topic', 'Other'),
                'ai_summary': categorization.get('summary', ''),
                'needs_human_attention': categorization.get('needs_human_attention', False),
                'reason': categorization.get('reason', ''),
                'draft_reply': None,
                'draft_id': None,
            }
            if email_result['urgency'] == 'High':
                email_result['needs_human_attention'] = True
            elif email_result['urgency'] in ['Medium', 'Low']:
                try:
                    email_result['draft_reply'] = self.draft_reply(email)
                except Exception as e:
                    print(f"Draft error: {e}")
            triaged.append(email_result)
        return triaged
