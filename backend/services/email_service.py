import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os

# --- CONFIGURATION ---
# ⚠️ SECURITY WARNING: In a real app, use environment variables for these!
SENDER_EMAIL = "your_email@gmail.com"  # The email SENDING the report
SENDER_PASSWORD = "your_app_password"  # Google App Password (NOT your normal password)
DOCTOR_EMAIL = "narutouk699@gmail.com" # The doctor receiving the report

def send_report_email(pdf_path: str, patient_name: str, session_id: int):
    """
    Sends the generated PDF report to the doctor via email.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found at {pdf_path}")
        return False

    try:
        # 1. Setup the Email
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = DOCTOR_EMAIL
        msg['Subject'] = f"Triage Report - {patient_name} (Session #{session_id})"

        body = f"""
        Hello Doctor,

        Attached is the triage report for patient: {patient_name}.
        
        Session ID: {session_id}
        Generated automatically by AI Triage Assistant.
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
        # Use port 587 for TLS
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()

        print(f"Email sent successfully to {DOCTOR_EMAIL}")
        return True

    except Exception as e:
        print(f"Failed to send email: {e}")
        return False