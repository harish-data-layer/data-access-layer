#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scheduler.py — Auto-pull from SAP on a schedule with email alerts on failure

USAGE:
    python scheduler.py

Edit the CONFIGURE HERE section to set the schedule.
Edit .env to set your email credentials.
"""
import os, sys, time, subprocess, smtplib, traceback
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


# ╔══════════════════════════════════════════════════════╗
# ║  EDIT HERE — Set your pull schedule                 ║
# ╚══════════════════════════════════════════════════════╝

# Set mode to "daily" (run at a fixed time) or "interval" (every N hours)
SCHEDULE_MODE    = "daily"
PULL_AT_TIME     = "09:00"      # used when mode = "daily"   (24h format)
PULL_EVERY_HOURS = 6            # used when mode = "interval"

# ══════════════════════════════════════════════════════════
# DO NOT EDIT BELOW THIS LINE
# ══════════════════════════════════════════════════════════

# Email settings (all loaded from .env)
FROM_EMAIL     = os.getenv("ALERT_FROM_EMAIL")
EMAIL_PASSWORD = os.getenv("ALERT_EMAIL_PASSWORD")
SMTP_HOST      = os.getenv("ALERT_SMTP_HOST", "smtp.gmail.com")
SMTP_PORT      = int(os.getenv("ALERT_SMTP_PORT", "587"))
TO_EMAILS      = os.getenv("ALERT_TO_EMAILS", "").split(",")  # comma-separated in .env

# Path to pull.py
PULL_SCRIPT = os.path.join(os.path.dirname(__file__), "pull.py")
PYTHON      = sys.executable


def send_failure_email(error_details: str):
    """Send a failure alert email to all recipients in TO_EMAILS."""
    if not FROM_EMAIL or not EMAIL_PASSWORD:
        print("  [EMAIL] Email credentials not set in .env. Skipping alert.")
        return

    now     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = f"[SAP PULL FAILED] Error at {now}"
    body    = f"""
Hello,

The SAP data pull job failed at {now}.

Error Details:
--------------
{error_details}

Please check the server and restart the scheduler if needed.

— SAP Auto Pull System
"""

    try:
        msg = MIMEMultipart()
        msg["From"]    = FROM_EMAIL
        msg["To"]      = ", ".join(TO_EMAILS)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(FROM_EMAIL, EMAIL_PASSWORD)
            server.sendmail(FROM_EMAIL, TO_EMAILS, msg.as_string())

        print(f"  [EMAIL] Failure alert sent to: {', '.join(TO_EMAILS)}")
    except Exception as e:
        print(f"  [EMAIL] Failed to send alert email: {e}")


def run_pull():
    """Run pull.py and send an email alert if it fails."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*55}")
    print(f"  [SCHEDULER] Pull started at {now}")
    print(f"{'='*55}")

    try:
        result = subprocess.run(
            [PYTHON, PULL_SCRIPT],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )

        # Always print the output
        if result.stdout: print(result.stdout)
        if result.stderr: print(result.stderr)

        if result.returncode == 0:
            print(f"  [SCHEDULER] Pull completed successfully.")
        else:
            # Pull script exited with an error — send failure email
            error_msg = result.stderr or result.stdout or "Unknown error (no output)"
            print(f"  [SCHEDULER] Pull failed! Sending failure email...")
            send_failure_email(
                f"Exit code: {result.returncode}\n\nOutput:\n{error_msg}"
            )

    except Exception:
        # Something went wrong running the script itself — send email
        error_details = traceback.format_exc()
        print(f"  [SCHEDULER] Unexpected error:\n{error_details}")
        send_failure_email(error_details)


# Set up the schedule
if SCHEDULE_MODE == "daily":
    schedule.every().day.at(PULL_AT_TIME).do(run_pull)
    print(f"  Schedule: Every day at {PULL_AT_TIME}")
elif SCHEDULE_MODE == "interval":
    schedule.every(PULL_EVERY_HOURS).hours.do(run_pull)
    print(f"  Schedule: Every {PULL_EVERY_HOURS} hours")


if __name__ == "__main__":
    print("=" * 55)
    print("  SAP AUTO-PULL SCHEDULER")
    print(f"  Mode     : {SCHEDULE_MODE}")
    print(f"  Alerts   : {', '.join(TO_EMAILS)}")
    print(f"  Script   : {PULL_SCRIPT}")
    print("=" * 55)
    print("\n  Scheduler running... (Ctrl+C to stop)")

    # Pull immediately on startup
    print("\n  Running initial pull on startup...")
    run_pull()

    # Then run on the configured schedule forever
    while True:
        schedule.run_pending()
        time.sleep(30)  # check every 30 seconds
