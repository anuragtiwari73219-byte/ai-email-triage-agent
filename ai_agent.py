"""
AI Triage Agent using LangChain + Google Gemini (gemini-2.0-flash).

Responsibilities:
1. Categorize emails by urgency (High/Medium/Low) and topic
2. Generate draft replies for Medium and Low urgency emails
3. Flag High urgency emails for human attention (no auto-draft)
"""

import json
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from config import GOOGLE_API_KEY


class EmailTriageAgent:
    """LangChain-powered email triage agent using Google Gemini."""

    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        """Lazy-initialize the LLM so the server can start without a valid API key."""
        if self._llm is None:
            if not GOOGLE_API_KEY or GOOGLE_API_KEY == 'your_google_api_key_here':
                raise ValueError(
                    "GOOGLE_API_KEY not set. Add it to your .env file."
                )
            self._llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=GOOGLE_API_KEY,
                temperature=0.1,
                max_tokens=2048,
            )
        return self._llm

    # ─── Email Categorization ───────────────────────────────────────────

    def categorize_email(self, email):
        """
        Analyze a single email and return categorization.
        Returns dict with: urgency, topic, summary, needs_human_attention, reason
        """
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are an expert AI email triage assistant. Analyze the given email and categorize it.

Return your response as a valid JSON object with exactly these fields:
- "urgency": one of "High", "Medium", "Low"
- "topic": one of "Work", "Finance", "Promotions", "Personal", "Spam"
- "summary": a concise 1-2 sentence summary of the email's content
- "needs_human_attention": boolean — true if this email requires a human to review and act on it
- "reason": brief explanation for the urgency classification

Urgency Guidelines:
- **High**: Urgent deadlines (within 24-48hrs), critical issues, security/breach alerts, financial emergencies, time-sensitive meeting requests, escalation emails, emails from executives/VIPs
- **Medium**: Regular work correspondence, bills/payment reminders, personal emails needing a response, scheduled meeting invites, account notifications
- **Low**: Newsletters, promotional offers, social media notifications, automated reports, marketing emails, subscription updates, spam

Return ONLY the JSON object. No markdown formatting, no code blocks, no extra text."""
            ),
            (
                "human",
                """Analyze this email:

From: {sender}
Subject: {subject}
Date: {date}

Body:
{body}"""
            ),
        ])

        chain = prompt | self.llm

        for attempt in range(4):
            try:
                response = chain.invoke({
                    "sender": email.get('from', 'Unknown'),
                    "subject": email.get('subject', '(No Subject)'),
                    "date": email.get('date', ''),
                    "body": (email.get('body') or email.get('snippet', ''))[:3000],
                })

                content = response.content.strip()

                # Strip markdown code fences if present
                if content.startswith('```'):
                    content = content.split('\n', 1)[1].rsplit('```', 1)[0].strip()
                if content.startswith('{'):
                    result = json.loads(content)
                else:
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    if start != -1 and end > start:
                        result = json.loads(content[start:end])
                    else:
                        raise ValueError("No JSON found in response")

                result.setdefault('urgency', 'Medium')
                result.setdefault('topic', 'Personal')
                result.setdefault('summary', email.get('snippet', '')[:100])
                result.setdefault('needs_human_attention', True)
                result.setdefault('reason', '')
                return result

            except Exception as e:
                if '429' in str(e) or 'quota' in str(e).lower() or 'rate' in str(e).lower():
                    wait = 5 * (2 ** attempt)
                    print(f"  [Rate limit] Waiting {wait}s before retry...")
                    time.sleep(wait)
                else:
                    print(f"[AI] Categorization error for '{email.get('subject', '?')}': {e}")
                    break
            return {
                "urgency": "Medium",
                "topic": "Personal",
                "summary": email.get('snippet', '')[:100],
                "needs_human_attention": True,
                "reason": f"Auto-categorization failed: {str(e)}",
            }

    # ─── Draft Reply Generation ──────────────────────────────────────────

    def draft_reply(self, email):
        """
        Generate a professional draft reply for a Medium/Low urgency email.
        The draft is meant to be reviewed by the user before sending.
        """
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are a professional email assistant drafting replies on behalf of the user.

Guidelines:
- Write a polite, professional, and concise reply
- Match the tone and formality of the original email
- For promotional emails: a brief acknowledgment or polite decline
- For routine work emails: address the main point directly
- For newsletters/notifications: a simple acknowledgment
- For personal emails: warm and friendly tone
- NEVER commit to meetings, deadlines, or financial decisions — instead say "I'll review and confirm shortly"
- Keep replies under 150 words
- Do NOT include subject line — only the reply body
- Do NOT include any meta-commentary about the draft

Return ONLY the reply text."""
            ),
            (
                "human",
                """Draft a reply for this email:

From: {sender}
Subject: {subject}
Date: {date}

Body:
{body}"""
            ),
        ])

        chain = prompt | self.llm

        for attempt in range(4):
            try:
                response = chain.invoke({
                    "sender": email.get('from', 'Unknown'),
                    "subject": email.get('subject', '(No Subject)'),
                    "date": email.get('date', ''),
                    "body": (email.get('body') or email.get('snippet', ''))[:3000],
                })
                return response.content.strip()
            except Exception as e:
                if '429' in str(e) or 'quota' in str(e).lower() or 'rate' in str(e).lower():
                    wait = 5 * (2 ** attempt)
                    print(f"  [Rate limit] Waiting {wait}s before retry...")
                    time.sleep(wait)
                else:
                    print(f"[AI] Draft generation error: {e}")
                    break
            return f"Thank you for your email. I've received your message regarding \"{email.get('subject', 'your inquiry')}\" and will get back to you shortly."

    # ─── Full Triage Pipeline ────────────────────────────────────────────

    def triage_inbox(self, emails, gmail_service=None):
        """
        Run the full triage pipeline on a list of emails:
        1. Categorize each email (urgency + topic)
        2. Flag High urgency emails with red label (no draft)
        3. Auto-draft replies for Medium and Low urgency emails
        """
        triaged = []

        for i, email in enumerate(emails):
            print(f"[Triage] Processing email {i+1}/{len(emails)}: {email.get('subject', '?')[:50]}")

            # Step 1: Categorize
            categorization = self.categorize_email(email)

            email_result = {
                **email,
                'urgency': categorization.get('urgency', 'Medium'),
                'topic': categorization.get('topic', 'Personal'),
                'ai_summary': categorization.get('summary', ''),
                'needs_human_attention': categorization.get('needs_human_attention', False),
                'reason': categorization.get('reason', ''),
                'draft_reply': None,
                'draft_id': None,
            }

            # Step 2: High urgency → flag only, NO auto-draft
            if email_result['urgency'] == 'High':
                email_result['needs_human_attention'] = True
                if gmail_service:
                    try:
                        gmail_service.add_urgent_label(email['id'])
                        print(f"  ⚑ Flagged as URGENT")
                    except Exception as e:
                        print(f"  ✗ Error flagging: {e}")

            # Step 3: Medium and Low urgency → auto-draft reply
            elif email_result['urgency'] in ['Medium', 'Low']:
                try:
                    draft_text = self.draft_reply(email)
                    email_result['draft_reply'] = draft_text

                    if gmail_service:
                        sender = email.get('from', '')
                        sender_email = (
                            sender.split('<')[1].rstrip('>')
                            if '<' in sender
                            else sender
                        )

                        draft = gmail_service.create_draft(
                            to=sender_email,
                            subject=email.get('subject', ''),
                            body=draft_text,
                            thread_id=email.get('thread_id'),
                        )
                        email_result['draft_id'] = draft.get('id')
                        print(f"  ✉ Draft created")
                except Exception as e:
                    print(f"  ✗ Error creating draft: {e}")

            triaged.append(email_result)

        return triaged
