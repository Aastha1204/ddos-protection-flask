import smtplib, os
from email.mime.text import MIMEText
from database import get_user_email

SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "your_email@gmail.com")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", None)  # prefer app password or env var

def send_email_alert(message):
    receiver_email = get_user_email()
    if not receiver_email:
        print("[EMAIL] No user email registered. Skipping alert.")
        return False

    if not SENDER_PASSWORD or "your_email" in SENDER_EMAIL:
        print("[EMAIL] Sender credentials not configured. Set SENDER_EMAIL and SENDER_PASSWORD as environment variables to enable real emails.")
        print(f"[EMAIL] Would send to {receiver_email}: {message}")
        return False

    try:
        msg = MIMEText(message)
        msg["Subject"] = "🚨 DDoS Attack Alert"
        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver_email

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print(f"[EMAIL] Alert sent to {receiver_email}: {message}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False
