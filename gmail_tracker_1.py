"""
Gmail Cold Email Tracker + Follow-up Drafter
=============================================
Author  : Ruchitha Yathirajulu
Purpose : Scans Gmail Sent folder for cold recruiter emails,
          checks for replies, flags unanswered emails after 7 days,
          and saves personalised follow-up drafts directly to Gmail.

Setup Instructions (README.md has full details):
  1. pip install -r requirements.txt
  2. Enable Gmail API at console.cloud.google.com
  3. Download credentials.json → place in this folder
  4. python gmail_tracker.py
"""

import os
import base64
import re
import json
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Google API libraries
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION — Edit these to match your needs
# ══════════════════════════════════════════════════════════════════════════════

FOLLOWUP_AFTER_DAYS = 3          # Flag emails with no reply after this many days

# Subject line keywords that identify cold recruiter/job emails
RECRUITER_SUBJECT_KEYWORDS = [
    "Application Interest - "
]

# Your name — used in follow-up email signature
YOUR_NAME = "Ruchitha Yathirajulu"
YOUR_EMAIL = ""   # filled automatically from Gmail

# Gmail API scope — allows reading + composing drafts
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

# ══════════════════════════════════════════════════════════════════════════════
# GMAIL AUTHENTICATION
# ══════════════════════════════════════════════════════════════════════════════

def authenticate_gmail():
    """
    Authenticate with Gmail API using OAuth 2.0.
    - First run: opens browser for you to log in and click Allow
    - Subsequent runs: uses saved token.json automatically
    """
    creds = None

    # Load saved credentials if they exist
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If no valid credentials, prompt login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                print("\n❌ credentials.json not found!")
                print("   Please follow the setup instructions in README.md")
                print("   to enable the Gmail API and download credentials.json\n")
                exit(1)
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for future runs
        with open("token.json", "w") as f:
            f.write(creds.to_json())

    print("✅ Gmail authenticated successfully\n")
    return build("gmail", "v1", credentials=creds)


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def get_header(message, name):
    """Extract a specific header value from an email message."""
    headers = message.get("payload", {}).get("headers", [])
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def parse_date(date_str):
    """Parse email date string into a datetime object."""
    if not date_str:
        return None
    # Clean up timezone abbreviations Gmail sometimes adds
    date_str = re.sub(r'\s*\([^)]*\)', '', date_str).strip()
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S",
        "%d %b %Y %H:%M:%S",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def extract_recipient_name(to_header):
    """
    Try to extract first name from To: header.
    e.g. 'John Smith <john@company.com>' → 'John'
    e.g. 'john@company.com' → 'there'
    """
    match = re.match(r'^([^<@,]+)', to_header.strip())
    if match:
        name = match.group(1).strip().strip('"')
        first = name.split()[0] if name else ""
        if first and first.replace(".", "").isalpha():
            return first
    return "there"


def extract_company(to_header, subject):
    """Try to extract company name from email domain or subject."""
    # Try email domain
    domain_match = re.search(r'@([\w\-]+)\.(com|ca|org|net|io)', to_header.lower())
    if domain_match:
        domain = domain_match.group(1)
        # Skip generic email providers
        if domain not in ["gmail", "yahoo", "hotmail", "outlook", "icloud"]:
            return domain.capitalize()
    return "your company"


def is_recruiter_email(subject):
    """Check if a sent email looks like a cold recruiter/job outreach."""
    subject_lower = subject.lower()
    return any(kw in subject_lower for kw in RECRUITER_SUBJECT_KEYWORDS)


# ══════════════════════════════════════════════════════════════════════════════
# CORE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_sent_recruiter_emails(service, max_results=100):
    """
    Fetch sent emails that look like cold recruiter outreach.
    Returns a list of email metadata dicts.
    """
    print("📬 Scanning your Sent folder for recruiter emails...")

    try:
        # Use query string to search sent folder — more reliable than labelIds
        results = service.users().messages().list(
            userId="me",
            q="in:sent subject:Application Interest",
            maxResults=max_results
        ).execute()
    except HttpError as e:
        print(f"❌ Error fetching emails: {e}")
        return []

    messages = results.get("messages", [])
    if not messages:
        # Fallback — try broader search
        try:
            results = service.users().messages().list(
                userId="me",
                labelIds=["SENT"],
                maxResults=max_results
            ).execute()
            messages = results.get("messages", [])
        except HttpError:
            pass

    if not messages:
        print("   No sent emails found.\n")
        return []

    recruiter_emails = []
    print(f"   Found {len(messages)} sent emails — filtering for recruiter emails...\n")

    for msg in messages:
        try:
            full_msg = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="metadata",
                metadataHeaders=["Subject", "To", "Date", "From", "Message-ID"]
            ).execute()

            subject = get_header(full_msg, "Subject")
            to      = get_header(full_msg, "To")
            date    = get_header(full_msg, "Date")
            frm     = get_header(full_msg, "From")
            msg_id  = get_header(full_msg, "Message-ID")

            # Accept all emails from this search since we already filtered by subject
            if not subject:
                continue

            sent_date = parse_date(date)
            if not sent_date:
                continue

            recruiter_emails.append({
                "id":          msg["id"],
                "thread_id":   full_msg.get("threadId"),
                "message_id":  msg_id,
                "subject":     subject,
                "to":          to,
                "from":        frm,
                "sent_date":   sent_date,
                "days_ago":    (datetime.now(timezone.utc) - sent_date).days,
            })

        except HttpError:
            continue

    print(f"   ✅ Found {len(recruiter_emails)} recruiter/job emails in Sent folder\n")
    return recruiter_emails


def check_for_replies(service, emails):
    """
    For each cold email, check if the thread has any replies.
    A reply = someone other than you responded in the same thread.
    """
    print("🔍 Checking for replies...")

    your_email = service.users().getProfile(userId="me").execute().get("emailAddress", "")

    for email in emails:
        try:
            thread = service.users().threads().get(
                userId="me",
                id=email["thread_id"],
                format="metadata",
                metadataHeaders=["From", "Date"]
            ).execute()

            messages_in_thread = thread.get("messages", [])

            # Check if any message in the thread was NOT sent by you
            has_reply = False
            for msg in messages_in_thread:
                sender = get_header(msg, "From")
                if your_email.lower() not in sender.lower():
                    has_reply = True
                    break

            email["has_reply"]   = has_reply
            email["your_email"]  = your_email
            email["needs_followup"] = (
                not has_reply and
                email["days_ago"] >= FOLLOWUP_AFTER_DAYS
            )

        except HttpError:
            email["has_reply"]      = False
            email["needs_followup"] = False

    replied   = sum(1 for e in emails if e.get("has_reply"))
    pending   = sum(1 for e in emails if not e.get("has_reply"))
    to_follow = sum(1 for e in emails if e.get("needs_followup"))

    print(f"   ✅ Replied:          {replied}")
    print(f"   ⏳ Awaiting reply:   {pending}")
    print(f"   🚨 Need follow-up:  {to_follow} (no reply after {FOLLOWUP_AFTER_DAYS}+ days)\n")

    return emails


def draft_followup_email(to, subject, recipient_name, company, days_ago, original_subject):
    """
    Generate a personalised follow-up email body.
    """
    # Clean up subject for reply
    reply_subject = subject if subject.startswith("Re:") else f"Re: {subject}"

    body = f"""Hi {recipient_name},

I hope you're doing well!

I wanted to follow up on my email from {days_ago} days ago regarding the {original_subject.lower()} opportunity at {company}.

I remain very enthusiastic about the possibility of joining {company} and contributing to your team. I believe my background in business analysis, data analytics, and project management — combined with my hands-on experience at AIMCo and my portfolio of BA case studies — would make me a strong fit.

I would love the opportunity to connect for a brief conversation at your convenience. Please let me know if you need any additional information from my end.

Thank you for your time and consideration. I look forward to hearing from you!

Best regards,
{YOUR_NAME}
📧 yathirajuluruchitha@gmail.com
📞 +1 (343) 558-9542
🔗 linkedin.com/in/ruchitha-yathirajulu-b87555191
🌐 ruchithayathiraj.github.io
"""
    return reply_subject, body


def save_draft_to_gmail(service, to, subject, body, thread_id):
    """
    Save a follow-up email as a Gmail Draft, threaded to the original email.
    """
    message = MIMEMultipart()
    message["to"]      = to
    message["subject"] = subject
    message.attach(MIMEText(body, "plain"))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    draft_body = {
        "message": {
            "raw":      raw,
            "threadId": thread_id
        }
    }

    draft = service.users().drafts().create(
        userId="me",
        body=draft_body
    ).execute()

    return draft.get("id")


# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY REPORT
# ══════════════════════════════════════════════════════════════════════════════

def print_summary(emails, drafted):
    """Print a clean summary report to the console."""
    total      = len(emails)
    replied    = sum(1 for e in emails if e.get("has_reply"))
    pending    = sum(1 for e in emails if not e.get("has_reply") and not e.get("needs_followup"))
    needs_fu   = sum(1 for e in emails if e.get("needs_followup"))
    reply_rate = round((replied / total * 100), 1) if total > 0 else 0

    print("\n" + "═" * 55)
    print("  📊 COLD EMAIL CAMPAIGN SUMMARY")
    print("═" * 55)
    print(f"  Total recruiter emails sent  : {total}")
    print(f"  ✅ Received a reply          : {replied} ({reply_rate}% reply rate)")
    print(f"  ⏳ Awaiting reply (<7 days)  : {pending}")
    print(f"  🚨 Need follow-up (7+ days)  : {needs_fu}")
    print(f"  ✉️  Follow-up drafts created  : {drafted}")
    print("═" * 55)

    if emails:
        print("\n  📋 EMAIL BREAKDOWN:")
        print(f"  {'Subject':<40} {'Days':<6} {'Status'}")
        print(f"  {'-'*40} {'-'*6} {'-'*15}")
        for e in sorted(emails, key=lambda x: x["days_ago"], reverse=True):
            status = "✅ Replied" if e.get("has_reply") else \
                     ("🚨 Follow-up drafted" if e.get("needs_followup") else "⏳ Waiting")
            subj = e["subject"][:38] + ".." if len(e["subject"]) > 40 else e["subject"]
            print(f"  {subj:<40} {e['days_ago']:<6} {status}")

    print("\n  💡 TIP: Go to Gmail Drafts to review and send your follow-ups!")
    print("═" * 55 + "\n")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "═" * 55)
    print("  Gmail Cold Email Tracker + Follow-up Drafter")
    print("  by Ruchitha Yathirajulu")
    print("═" * 55 + "\n")

    # Step 1 — Authenticate
    service = authenticate_gmail()

    # Step 2 — Fetch sent recruiter emails
    emails = get_sent_recruiter_emails(service)
    if not emails:
        print("No recruiter emails found. Try sending some cold emails first!")
        return

    # Step 3 — Check for replies
    emails = check_for_replies(service, emails)

    # Step 4 — Draft follow-ups for emails needing one
    to_followup = [e for e in emails if e.get("needs_followup")]

    if not to_followup:
        print("🎉 Great news — no follow-ups needed right now!")
    else:
        print(f"✉️  Creating {len(to_followup)} follow-up draft(s) in Gmail...\n")

    drafted = 0
    for email in to_followup:
        recipient_name = extract_recipient_name(email["to"])
        company        = extract_company(email["to"], email["subject"])
        reply_subject, body = draft_followup_email(
            to               = email["to"],
            subject          = email["subject"],
            recipient_name   = recipient_name,
            company          = company,
            days_ago         = email["days_ago"],
            original_subject = email["subject"]
        )

        try:
            draft_id = save_draft_to_gmail(
                service    = service,
                to         = email["to"],
                subject    = reply_subject,
                body       = body,
                thread_id  = email["thread_id"]
            )
            print(f"  ✅ Draft created → {email['subject'][:45]}...")
            email["draft_id"] = draft_id
            drafted += 1
        except HttpError as e:
            print(f"  ❌ Failed to draft: {email['subject'][:45]}... | Error: {e}")

    # Step 5 — Print summary
    print_summary(emails, drafted)


if __name__ == "__main__":
    main()