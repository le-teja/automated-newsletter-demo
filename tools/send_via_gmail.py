#!/usr/bin/env python3
"""Send the newsletter to subscribers via Gmail API. Reads list from Google Sheets."""

import argparse
import base64
import os
import sys
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "..", "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "..", "token.json")


def get_google_credentials():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(
                    f"Error: credentials.json not found at {CREDENTIALS_FILE}\n"
                    "Download it from Google Cloud Console > APIs & Services > Credentials.",
                    file=sys.stderr,
                )
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return creds


def get_subscribers(sheet_id: str, creds) -> list[dict]:
    from googleapiclient.discovery import build

    service = build("sheets", "v4", credentials=creds)
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range="A2:C1000")
        .execute()
    )
    rows = result.get("values", [])
    subscribers = []
    for row in rows:
        if len(row) < 1:
            continue
        email = row[0].strip() if len(row) > 0 else ""
        name = row[1].strip() if len(row) > 1 else "Subscriber"
        status = row[2].strip().lower() if len(row) > 2 else "active"
        if email and status == "active":
            subscribers.append({"email": email, "name": name})
    return subscribers


def build_mime_message(
    html_content: str,
    plain_content: str,
    subject: str,
    to_email: str,
    to_name: str,
    from_email: str,
) -> str:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_email}"
    msg["To"] = to_email

    # Personalize plain text
    personalized_plain = plain_content.replace("Hi Subscriber,", f"Hi {to_name},")
    personalized_html = html_content.replace("Hi Subscriber,", f"Hi {to_name},")

    msg.attach(MIMEText(personalized_plain, "plain", "utf-8"))
    msg.attach(MIMEText(personalized_html, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
    return raw


def send_one(gmail_service, raw_message: str) -> bool:
    try:
        gmail_service.users().messages().send(
            userId="me", body={"raw": raw_message}
        ).execute()
        return True
    except Exception as e:
        print(f"  Send failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Send newsletter via Gmail to Google Sheets subscribers")
    parser.add_argument("html_file", help="Path to newsletter.html")
    parser.add_argument("plain_file", help="Path to newsletter_plain.txt")
    parser.add_argument("subject", help="Email subject line")
    parser.add_argument("--sheet-id", default=os.environ.get("GOOGLE_SHEETS_SUBSCRIBER_ID"), help="Google Sheets ID")
    parser.add_argument("--from-email", default=os.environ.get("GMAIL_FROM", ""), help="Sender email address")
    parser.add_argument("--dry-run", action="store_true", help="List subscribers without sending")
    args = parser.parse_args()

    if not args.sheet_id:
        print("Error: GOOGLE_SHEETS_SUBSCRIBER_ID not set in .env or --sheet-id not provided", file=sys.stderr)
        sys.exit(1)

    with open(args.html_file, encoding="utf-8") as f:
        html_content = f.read()
    with open(args.plain_file, encoding="utf-8") as f:
        plain_content = f.read()

    print("Authenticating with Google...")
    creds = get_google_credentials()

    print(f"Fetching subscriber list from sheet: {args.sheet_id}")
    subscribers = get_subscribers(args.sheet_id, creds)
    print(f"Found {len(subscribers)} active subscriber(s)")

    if not subscribers:
        print("No active subscribers found. Check your Google Sheet format.")
        sys.exit(0)

    if args.dry_run:
        print("\nDRY RUN — would send to:")
        for s in subscribers:
            print(f"  {s['name']} <{s['email']}>")
        sys.exit(0)

    from googleapiclient.discovery import build
    gmail = build("gmail", "v1", credentials=creds)

    from_email = args.from_email
    if not from_email:
        # Auto-detect authenticated user's email
        profile = gmail.users().getProfile(userId="me").execute()
        from_email = profile.get("emailAddress", "")

    sent_count = 0
    failed = []

    for sub in subscribers:
        raw = build_mime_message(
            html_content=html_content,
            plain_content=plain_content,
            subject=args.subject,
            to_email=sub["email"],
            to_name=sub["name"],
            from_email=from_email,
        )
        success = send_one(gmail, raw)
        if success:
            sent_count += 1
            print(f"  Sent to {sub['name']} <{sub['email']}>")
        else:
            failed.append(sub["email"])
        time.sleep(0.3)  # Stay well within Gmail API rate limits (250 quota units/sec)

    print(f"\nDone: {sent_count} sent, {len(failed)} failed")
    if failed:
        print("Failed addresses:")
        for addr in failed:
            print(f"  {addr}")


if __name__ == "__main__":
    main()
