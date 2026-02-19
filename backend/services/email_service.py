import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

# --- SECURE CONFIGURATION FROM ENVIRONMENT ---
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_APP_PASSWORD")
DOCTOR_EMAIL = os.getenv("DOCTOR_EMAIL")

# Validation check
if not all([SENDER_EMAIL, SENDER_PASSWORD, DOCTOR_EMAIL]):
    raise ValueError(
        "Missing email configuration! Please set SENDER_EMAIL, "
        "SENDER_APP_PASSWORD, and DOCTOR_EMAIL in your .env file"
    )


def send_report_email(
        pdf_path: str,
        patient_name: str,
        session_id: int,
        recipient_email: Optional[str] = None
) -> dict:
    """
    Sends the generated PDF report to the doctor via email.

    Args:
        pdf_path: Path to the PDF file
        patient_name: Patient's name
        session_id: Session identifier
        recipient_email: Optional override for doctor's email

    Returns:
        dict: {"success": bool, "message": str}
    """
    # Use provided email or default doctor email
    recipient = recipient_email or DOCTOR_EMAIL

    # Validation
    if not os.path.exists(pdf_path):
        error_msg = f"❌ Error: PDF not found at {pdf_path}"
        print(error_msg)
        return {"success": False, "message": error_msg}

    if not recipient:
        error_msg = "❌ Error: No recipient email provided"
        print(error_msg)
        return {"success": False, "message": error_msg}

    try:
        # 1. Setup the Email
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient
        msg['Subject'] = f"Patient Pre-Consultation Report - {patient_name} (Session #{session_id})"

        # Email body with better formatting
        body = f"""
Hello Doctor,

Attached is the pre-consultation report for:

Patient Name: {patient_name}
Session ID: {session_id}
Report Generated: {os.path.basename(pdf_path)}

This report was generated automatically by the AI-Powered Patient Pre-Consultation System.

Please review the symptoms before the patient's consultation.

---
This is an automated message. Please do not reply to this email.
        """
        msg.attach(MIMEText(body, 'plain'))

        # 2. Attach the PDF
        with open(pdf_path, "rb") as f:
            pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
            pdf_attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=os.path.basename(pdf_path)
            )
            msg.attach(pdf_attachment)

        # 3. Connect to Gmail Server and Send
        print(f"📧 Connecting to Gmail server...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()

        print(f"🔐 Logging in as {SENDER_EMAIL}...")
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        print(f"📤 Sending email to {recipient}...")
        server.send_message(msg)
        server.quit()

        success_msg = f"✅ Email sent successfully to {recipient}"
        print(success_msg)
        return {"success": True, "message": success_msg}

    except smtplib.SMTPAuthenticationError:
        error_msg = "❌ Authentication failed. Check your email and app password."
        print(error_msg)
        return {"success": False, "message": error_msg}

    except smtplib.SMTPException as e:
        error_msg = f"❌ SMTP error occurred: {str(e)}"
        print(error_msg)
        return {"success": False, "message": error_msg}

    except Exception as e:
        error_msg = f"❌ Unexpected error: {str(e)}"
        print(error_msg)
        return {"success": False, "message": error_msg}


def test_email_configuration():
    """
    Test if email configuration is working
    """
    print("🧪 Testing email configuration...")
    print(f"Sender: {SENDER_EMAIL}")
    print(f"Recipient: {DOCTOR_EMAIL}")
    print(f"Password set: {'Yes' if SENDER_PASSWORD else 'No'}")

    if not SENDER_PASSWORD:
        print("❌ App password not set!")
        return False

    print("✅ Configuration loaded successfully")
    return True


if __name__ == "__main__":
    # Test configuration when run directly
    test_email_configuration()