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

    def decide_action(self, email, categorization):
        """
        Agent decides which action to take based on the email content and
        its classification. Returns dict: {"action": ..., "reasoning": ...}
        Action is one of: draft_reply, flag_urgent, archive_silently.

        NOTE: LLM tool-choice for this step was empirically tested (5-run
        consistency check) and found ~40% inconsistent on ambiguous
        Personal/Networking emails already flagged as needing attention
        (same input, model alternated between draft_reply and
        archive_silently). A deterministic override below closes that gap
        rather than relying purely on prompt wording, which did not fix it.
        """
        tools = [
            {
                "name": "draft_reply",
                "description": "Use this when the email is a genuine personal message, a networking message, or an application-status update that expects or invites a response from the user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string", "description": "Why this action was chosen."}
                    },
                    "required": ["reasoning"],
                },
            },
            {
                "name": "flag_urgent",
                "description": "Use this when the email is time-sensitive and needs the user's direct attention right now — interview calls, deadlines, urgent job alerts, anything blocking.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string", "description": "Why this action was chosen."}
                    },
                    "required": ["reasoning"],
                },
            },
            {
                "name": "archive_silently",
                "description": "Use this for newsletters, promotional content, spam, or automated notifications that need no response and no attention.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string", "description": "Why this action was chosen."}
                    },
                    "required": ["reasoning"],
                },
            },
        ]

        llm_with_tools = self.llm.bind_tools(tools, tool_choice="required")

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an email triage agent deciding what action to take on an email.
You have already classified this email — use that classification plus the raw content to pick exactly ONE action tool.
Do not just mirror the urgency label mechanically; consider the actual content too.

Examples:
- A personal message asking to meet up, catch up, or requesting information -> draft_reply (it expects a response)
- A newsletter or promotional content with no action needed -> archive_silently
- A time-sensitive item (interview, deadline, urgent request) -> flag_urgent

Your chosen tool MUST match your own reasoning. If your reasoning describes why a reply is needed, you must call draft_reply — do not reason toward one action and then call a different tool.

You MUST call exactly one tool."""),
            ("human", """From: {sender}
Subject: {subject}
Body:
{body}

Classification:
- Topic: {topic}
- Urgency: {urgency}
- Summary: {summary}

Pick the single correct action tool."""),
        ])

        chain = prompt | llm_with_tools
        last_error = None

        for attempt in range(4):
            try:
                response = chain.invoke({
                    "sender": email.get('from', 'Unknown'),
                    "subject": email.get('subject', ''),
                    "body": (email.get('body') or email.get('snippet', ''))[:3000],
                    "topic": categorization.get('topic', 'Other'),
                    "urgency": categorization.get('urgency', 'Medium'),
                    "summary": categorization.get('summary', ''),
                })

                if not response.tool_calls:
                    raise ValueError("No tool call returned by model")

                call = response.tool_calls[0]
                action_name = call['name']
                reasoning = call['args'].get('reasoning', '')

                if action_name not in ('draft_reply', 'flag_urgent', 'archive_silently'):
                    raise ValueError(f"Unknown tool returned: {action_name}")

                # Deterministic guardrail — see note in docstring above.
                # Personal/Networking emails already flagged as needing
                # human attention must not be silently archived, regardless
                # of what the LLM's tool call says.
                if (action_name == 'archive_silently'
                        and categorization.get('topic') in ('Personal', 'Networking')
                        and categorization.get('needs_human_attention')):
                    action_name = 'draft_reply'
                    reasoning = f"[override: topic requires attention] {reasoning}"

                return {"action": action_name, "reasoning": reasoning}

            except Exception as e:
                last_error = e
                if '429' in str(e) or 'quota' in str(e).lower():
                    time.sleep(5 * (2 ** attempt))
                else:
                    break

        # Safe fallback: flag for human review rather than silently archiving.
        return {
            "action": "flag_urgent",
            "reasoning": f"Fallback due to error: {last_error}",
        }

    def draft_reply(self, email):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional email assistant. Write a concise reply under 150 words. Always sign the reply as "Anurag Tiwari" — never use a placeholder like "[Your Name]". Return ONLY the reply text."""),
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
            decision = self.decide_action(email, categorization)

            email_result = {
                **email,
                'urgency': categorization.get('urgency', 'Medium'),
                'topic': categorization.get('topic', 'Other'),
                'ai_summary': categorization.get('summary', ''),
                'needs_human_attention': categorization.get('needs_human_attention', False),
                'reason': categorization.get('reason', ''),
                'agent_action': decision['action'],
                'agent_reasoning': decision['reasoning'],
                'draft_reply': None,
                'draft_id': None,
            }

            if decision['action'] == 'flag_urgent':
                email_result['needs_human_attention'] = True
            elif decision['action'] == 'draft_reply':
                try:
                    email_result['draft_reply'] = self.draft_reply(email)
                except Exception as e:
                    print(f"Draft error: {e}")
            elif decision['action'] == 'archive_silently':
                email_result['needs_human_attention'] = False

            triaged.append(email_result)
        return triaged