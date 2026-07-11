"""
AI Email Triage Agent — Flask Application

Serves the web dashboard and exposes API endpoints for:
- Gmail OAuth authentication
- Email fetching and AI triage
- Manual draft creation
"""

import threading
from flask import Flask, render_template, jsonify, request
from gmail_service import GmailService
from ai_agent import EmailTriageAgent
from config import MAX_EMAILS, FLASK_HOST, FLASK_PORT, FLASK_DEBUG

# ─── App Setup ───────────────────────────────────────────────────────────────
app = Flask(__name__)

gmail = GmailService()
agent = EmailTriageAgent()

# Startup auto-authentication removed for security -- do not load a personal token globally.

# In-memory store for triaged emails
triage_store = {
    'emails': [],
    'processing': False,
    'error': None,
    'progress': 0,
    'total': 0,
}


# ─── Page Routes ─────────────────────────────────────────────────────────────

@app.route('/')
def dashboard():
    """Serve the main dashboard page."""
    return render_template('dashboard.html')


# ─── Auth API ────────────────────────────────────────────────────────────────

@app.route('/api/auth', methods=['POST'])
def authenticate():
    """Initiate Gmail OAuth 2.0 authentication."""
    try:
        gmail.authenticate()
        return jsonify({
            'status': 'authenticated',
            'email': gmail.user_email,
        })
    except FileNotFoundError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/auth/status')
def auth_status():
    """Check current authentication status."""
    return jsonify({
        'authenticated': gmail.is_authenticated(),
        'email': gmail.user_email if gmail.is_authenticated() else None,
    })


# ─── Triage API ──────────────────────────────────────────────────────────────

@app.route('/api/triage', methods=['POST'])
def run_triage():
    """
    Kick off the email triage pipeline in a background thread.
    Returns immediately with processing status.
    """
    if not gmail.is_authenticated():
        return jsonify({'error': 'Not authenticated. Connect Gmail first.'}), 401

    if triage_store['processing']:
        return jsonify({'error': 'Triage already in progress. Please wait.'}), 409

    def _process():
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading
        import time

        triage_store['processing'] = True
        triage_store['error'] = None
        triage_store['progress'] = 0

        try:
            print(f"\n{'='*60}")
            print(f"  Fetching up to {MAX_EMAILS} emails from inbox...")
            print(f"{'='*60}\n")

            emails = gmail.get_emails(max_results=MAX_EMAILS)
            triage_store['total'] = len(emails)
            print(f"  Found {len(emails)} emails. Starting parallel AI triage...\n")

            triaged_map = {}
            lock = threading.Lock()

            def process_one(idx_email):
                i, email = idx_email
                print(f"[{i+1}/{len(emails)}] {email.get('subject', '?')[:60]}")

                categorization = agent.categorize_email(email)

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

                # High urgency → flag only
                if email_result['urgency'] == 'High':
                    email_result['needs_human_attention'] = True
                    try:
                        gmail.add_urgent_label(email['id'])
                        print(f"  [!] Flagged URGENT: {email.get('subject','')[:40]}")
                    except Exception as e:
                        print(f"  [X] Flag error: {e}")

                # Medium / Low → auto-draft
                elif email_result['urgency'] in ['Medium', 'Low']:
                    try:
                        draft_text = agent.draft_reply(email)
                        email_result['draft_reply'] = draft_text

                        sender = email.get('from', '')
                        sender_email = (
                            sender.split('<')[1].rstrip('>')
                            if '<' in sender
                            else sender
                        )
                        draft = gmail.create_draft(
                            to=sender_email,
                            subject=email.get('subject', ''),
                            body=draft_text,
                            thread_id=email.get('thread_id'),
                        )
                        email_result['draft_id'] = draft.get('id')
                        print(f"  [D] Draft saved: {email.get('subject','')[:40]}")
                    except Exception as e:
                        print(f"  [X] Draft error: {e}")

                with lock:
                    triaged_map[i] = email_result
                    triage_store['progress'] = len(triaged_map)

                return i, email_result

            # Run up to 3 emails in parallel (respects Gemini free tier limits)
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(process_one, (i, e)) for i, e in enumerate(emails)]
                for future in as_completed(futures):
                    future.result()  # surfaces exceptions

            # Restore original order
            triaged = [triaged_map[i] for i in range(len(emails))]
            triage_store['emails'] = triaged

            print(f"\n{'='*60}")
            print(f"  [OK] Triage complete! {len(triaged)} emails processed.")
            print(f"{'='*60}\n")

        except Exception as e:
            triage_store['error'] = str(e)
            print(f"\n  [X] Triage failed: {e}\n")
        finally:
            triage_store['processing'] = False

    thread = threading.Thread(target=_process, daemon=True)
    thread.start()

    return jsonify({'status': 'processing', 'message': 'Triage started...'})


@app.route('/api/triage/status')
def triage_status():
    """Get current triage processing status."""
    return jsonify({
        'processing': triage_store['processing'],
        'error': triage_store['error'],
        'progress': triage_store['progress'],
        'total': triage_store['total'],
        'email_count': len(triage_store['emails']),
    })


@app.route('/api/emails')
def get_emails():
    """Get all triaged emails."""
    return jsonify({
        'emails': triage_store['emails'],
        'processing': triage_store['processing'],
    })


# ─── Draft API ───────────────────────────────────────────────────────────────

@app.route('/api/draft', methods=['POST'])
def create_draft():
    """Manually generate and save a draft reply for a specific email."""
    if not gmail.is_authenticated():
        return jsonify({'error': 'Not authenticated.'}), 401

    data = request.json
    email_id = data.get('email_id')

    if not email_id:
        return jsonify({'error': 'Missing email_id.'}), 400

    # Find the email in the triage store
    target_email = None
    for e in triage_store['emails']:
        if e['id'] == email_id:
            target_email = e
            break

    if not target_email:
        return jsonify({'error': 'Email not found in triage results.'}), 404

    try:
        # Generate draft with AI
        draft_text = agent.draft_reply(target_email)

        # Parse sender email
        sender = target_email.get('from', '')
        sender_email = (
            sender.split('<')[1].rstrip('>')
            if '<' in sender
            else sender
        )

        # Save as Gmail draft
        draft = gmail.create_draft(
            to=sender_email,
            subject=target_email.get('subject', ''),
            body=draft_text,
            thread_id=target_email.get('thread_id'),
        )

        # Update the store
        target_email['draft_reply'] = draft_text
        target_email['draft_id'] = draft.get('id')

        return jsonify({
            'status': 'success',
            'draft_reply': draft_text,
            'draft_id': draft.get('id'),
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("")
    print("  +----------------------------------------------------------+")
    print("  |           AI Email Triage Agent v1.0                     |")
    print("  |           --------------------------------               |")
    print("  |   Open http://localhost:5000 in your browser             |")
    print("  |   Connect Gmail -> Run Triage -> Review Results          |")
    print("  +----------------------------------------------------------+")
    print("")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
