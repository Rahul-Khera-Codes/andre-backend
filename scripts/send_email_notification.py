from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import smtplib

from dotenv import load_dotenv

load_dotenv()

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_USE_TLS = bool(os.getenv("EMAIL_USE_TLS"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")


# --- Your credentials ---
EMAIL_HOST = EMAIL_HOST
EMAIL_PORT = EMAIL_PORT
EMAIL_ADDRESS = EMAIL_HOST_USER   # Your Outlook alias/email
EMAIL_PASSWORD = EMAIL_HOST_PASSWORD      # Your App Password (NOT normal password)

# --- Email details ---
TO_EMAIL = EMAIL_HOST_USER
SUBJECT = "Test Email from Python"
BODY = "Hello,\n\nThis is a test email sent from Python using Microsoft Outlook SMTP with App Password.\n\nCheers!"

# --- Build email ---
msg = MIMEMultipart()
msg["From"] = EMAIL_ADDRESS
msg["To"] = TO_EMAIL
msg["Subject"] = SUBJECT
msg.attach(MIMEText(BODY, "plain"))

try:
    # Connect to Microsoft SMTP
    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
    server.starttls()  # Upgrade to secure connection
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.sendmail(EMAIL_ADDRESS, TO_EMAIL, msg.as_string())
    server.quit()
    print("✅ Email sent successfully!")

except smtplib.SMTPAuthenticationError as e:
    print("❌ Authentication failed:", e)
except Exception as e:
    print("❌ Error:", e)
