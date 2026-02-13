#!/usr/bin/env python3
"""Quick Gmail checker using IMAP + app password.
Prints unread message summaries (sender, subject, date).
"""

import email
import imaplib
import json
from email.header import decode_header, make_header
from pathlib import Path

SECRETS_PATH = Path(__file__).resolve().parent.parent / "secrets" / "gmail.json"
MAX_RESULTS = 20

def load_credentials():
    data = json.loads(SECRETS_PATH.read_text())
    return (
        data["email"],
        data["app_password"],
        data.get("imap_host", "imap.gmail.com"),
        data.get("imap_port", 993),
    )


def format_header(raw):
    if not raw:
        return "(no subject)"
    try:
        return str(make_header(decode_header(raw)))
    except Exception:
        return raw


def main():
    email_addr, app_password, imap_host, imap_port = load_credentials()
    app_password = app_password.replace(" ", "")  # Some providers format app passwords with spaces
    with imaplib.IMAP4_SSL(imap_host, imap_port) as imap_conn:
        imap_conn.login(email_addr, app_password)
        imap_conn.select("INBOX")
        status, data = imap_conn.search(None, "UNSEEN")
        if status != "OK":
            raise SystemExit("Failed to search inbox")

        ids = data[0].split()
        if not ids:
            print("✅ Inbox is clear — no unread messages.")
            return

        latest = ids[-MAX_RESULTS:]
        print(f"📬 {len(ids)} unread message(s). Showing {len(latest)} most recent:\n")
        for num in reversed(latest):
            status, msg_data = imap_conn.fetch(num, "(RFC822)")
            if status != "OK":
                print(f"- Could not fetch message {num.decode()} (status {status})")
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            subject = format_header(msg.get("Subject"))
            sender = format_header(msg.get("From"))
            date = msg.get("Date", "")
            print(f"- {subject}\n  From: {sender}\n  Date: {date}\n")


if __name__ == "__main__":
    main()
