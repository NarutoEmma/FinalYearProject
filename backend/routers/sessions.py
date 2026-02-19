#validate access code, create session and prevent multiple sessions
import os
from fastapi import APIRouter, Depends, HTTPException
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
    Start a new session using an access code
    """
    appointment = db.query(model.Appointment).filter(
        model.Appointment.access_code == payload.access_code,
        model.Appointment.status == "scheduled"
    ).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Invalid access code")

    # Prevent multiple sessions for same appointment
    existing_session = db.query(model.Session).filter(
        model.Session.appointment_id == appointment.id
    ).first()

    if existing_session:
        raise HTTPException(status_code=400, detail="Session already in progress")

    # Create session
    session = model.Session(
        appointment_id=appointment.id,
        started_at=datetime.now()
    )

    appointment.status = "in_progress"

    db.add(session)
    db.commit()
    db.refresh(session)

    print(f"✅ Session {session.id} started for appointment {appointment.id}")

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