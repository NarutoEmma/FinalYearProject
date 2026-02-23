#validate access code, create session and prevent multiple sessions
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime

from backend.app.database import get_db
from backend.app import schemas, model
from backend.services.pdf_generator import generate_summary_pdf
from backend.services.email_service import send_report_email

router = APIRouter(tags=["sessions"])

@router.post("/start", response_model=schemas.SessionResponse)
def start_session(payload: schemas.SessionCreate, db: Session = Depends(get_db)):
    """
    Start a new session OR resume an existing active session
    """
    # 1. Find appointment by access code (any status except completed)
    appointment = db.query(model.Appointment).filter(
        model.Appointment.access_code == payload.access_code,
        model.Appointment.status.in_(["scheduled", "in_progress"])  # ← Allow both!
    ).first()

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Invalid access code or appointment already completed"
        )

    # 2. Check if there's already an active session
    existing_session = db.query(model.Session).filter(
        model.Session.appointment_id == appointment.id,
        model.Session.ended_at == None  # ← Only check for active sessions
    ).first()

    if existing_session:
        # ✅ RESUME the existing session instead of creating new one
        print(f"🔄 Resuming existing session {existing_session.id}")

        return {
            "id": existing_session.id,
            "appointment_id": appointment.id,
            "message": "Session resumed",  # ← Different message
            "started_at": existing_session.started_at,
            "ended_at": None
        }

    # 3. Create new session (first time using code)
    session = model.Session(
        appointment_id=appointment.id,
        started_at=datetime.now()
    )

    appointment.status = "in_progress"

    db.add(session)
    db.commit()
    db.refresh(session)

    print(f"✅ New session {session.id} started for appointment {appointment.id}")

    return {
        "id": session.id,
        "appointment_id": appointment.id,
        "message": "Session started",
        "started_at": session.started_at,
        "ended_at": None
    }


@router.post("/{session_id}/finalize")
def finalize_session(session_id: int, db: Session = Depends(get_db)):
    """
    Finalize session, generate PDF report, and update appointment status
    """
    # 1. Get session
    session = db.query(model.Session).filter(
        model.Session.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Check if already finalized
    if session.ended_at:
        raise HTTPException(status_code=400, detail="Session already finalized")

    # 3. Get summary with symptoms
    summary_row = db.query(model.Summary).filter(
        model.Summary.session_id == session_id
    ).first()

    if not summary_row or not summary_row.summary_content:
        raise HTTPException(
            status_code=404,
            detail="No summary found for this session"
        )

    symptom_list = summary_row.summary_content.get("symptoms", [])

    # 4. Validate symptoms exist
    if not symptom_list:
        raise HTTPException(
            status_code=400,
            detail="No symptoms recorded. Please report symptoms first."
        )

    # 5. Get patient name
    patient_name = "patient"
    if session.appointment and session.appointment.user:
        patient_name = session.appointment.user.full_name

    # 6. Generate PDF
    report_dir = "reports"
    os.makedirs(report_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"symptom_report_{session_id}_{timestamp}.pdf"
    file_path = os.path.join(report_dir, filename)

    try:
        print(f"🔄 Generating PDF for session {session_id}...")
        generate_summary_pdf(session_id, patient_name, symptom_list, file_path)
        print(f"✅ PDF generated successfully: {file_path}")
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {str(e)}"
        )

    # 7. Send email (optional - won't fail if email fails)
    email_sent = False
    try:
        email_result = send_report_email(file_path, patient_name, session_id)

        # Handle both dict and boolean return types
        if isinstance(email_result, dict):
            email_sent = email_result.get("success", False)
        else:
            email_sent = email_result

        if email_sent:
            print(f"✅ Email sent successfully")
        else:
            print(f"⚠️ Email not sent, but PDF was generated")
    except Exception as e:
        print(f"⚠️ Email error: {e}")
        email_sent = False

    # 8. ✅ CRITICAL: Mark session as ended AND update appointment status
    print(f"⏰ Ending session {session_id}...")
    session.ended_at = datetime.now()

    # ✅ UPDATE APPOINTMENT STATUS TO COMPLETED
    if session.appointment:
        print(f"📅 Updating appointment {session.appointment.id} to completed...")
        session.appointment.status = "completed"
        print(f"✅ Appointment status updated to: {session.appointment.status}")

    # 9. Commit all changes to database
    db.commit()

    print(f"✅ Session {session_id} finalized successfully")
    print(f"   Session ended at: {session.ended_at}")
    print(f"   Appointment status: {session.appointment.status if session.appointment else 'N/A'}")
    print(f"   PDF path: {file_path}")
    print("=" * 60)

    # 10. Return success response
    return {
        "status": "success",
        "message": "Session finalized, PDF generated, and sent to doctor",
        "session_id": session_id,
        "pdf_path": file_path,
        "pdf_generated": True,
        "email_sent": email_sent,
        "ended_at": session.ended_at.isoformat(),
        "appointment_status": session.appointment.status if session.appointment else None,
        "symptoms_count": len(symptom_list)
    }

@router.get("/{session_id}/download-pdf")
def download_pdf(session_id: int, db: Session = Depends(get_db)):
    """
    Download the PDF report for a session (for patient to save to their phone)
    """
    # 1. Validate session exists
    session = db.query(model.Session).filter(
        model.Session.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Check if session has been finalized
    if not session.ended_at:
        raise HTTPException(
            status_code=400,
            detail="Session not finalized yet. Please finalize the session first."
        )

    # 3. Find the PDF file in reports directory
    report_dir = "reports"

    if not os.path.exists(report_dir):
        raise HTTPException(
            status_code=500,
            detail="Reports directory not found"
        )

    # Look for any PDF with this session ID
    try:
        pdf_files = [
            f for f in os.listdir(report_dir)
            if f.startswith(f"symptom_report_{session_id}") and f.endswith(".pdf")
        ]
    except Exception as e:
        print(f"❌ Error reading reports directory: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error accessing reports directory"
        )

    if not pdf_files:
        raise HTTPException(
            status_code=404,
            detail="PDF report not found. The report may have been deleted."
        )

    # 4. Get the most recent PDF if multiple exist (sorted by name, newest first)
    pdf_files.sort(reverse=True)
    pdf_filename = pdf_files[0]
    pdf_path = os.path.join(report_dir, pdf_filename)

    # 5. Verify file exists
    if not os.path.exists(pdf_path):
        raise HTTPException(
            status_code=404,
            detail="PDF file not found on server"
        )

    print(f"📥 Patient downloading PDF: {pdf_path}")
    print(f"   Session ID: {session_id}")
    print(f"   File size: {os.path.getsize(pdf_path)} bytes")

    # 6. Return the file for download
    return FileResponse(
        path=pdf_path,
        filename=pdf_filename,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{pdf_filename}"'
        }
    )