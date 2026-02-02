#validate access code, create session and prevent multiple sessions
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from backend.app.database import get_db
from backend.app import schemas, model
from backend.services.pdf_generator import generate_summary_pdf
from backend.services.email_service import send_report_email
router = APIRouter( tags=["sessions"])

@router.post("/start", response_model=schemas.SessionResponse)
def start_session(payload:schemas.SessionCreate,
                  db: Session = Depends(get_db)):

    appointment = db.query(model.Appointment).filter(
        model.Appointment.access_code == payload.access_code,
        model.Appointment.status=="scheduled").first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Invalid access code")

    #prevent multiple sessions for same appointment
    existing_session = db.query(model.Session).filter(
        model.Session.appointment_id == appointment.id).first()
    if existing_session:
        raise HTTPException(status_code=400, detail="session already in progress")

    #create session
    session = model.Session(appointment_id=appointment.id,
                            started_at=datetime.now())

    appointment.status="in_progress"

    db.add(session)
    db.commit()
    db.refresh(session)
    return {"id": session.id,
            "appointment_id": appointment.id,
            "message": "session started",
            "started_at": session.started_at,
            "ended_at": None}


@router.post("/{session_id}/finalize")
def finalize_session(session_id:int, db: Session = Depends(get_db)):
    session = db.query(model.Session).filter(
        model.Session.id==session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    summary_row = db.query(model.Summary).filter(
        model.Summary.session_id==session_id).first()
    if not summary_row or not summary_row.summary_content:
        raise HTTPException(status_code=404, detail="No summary found for this session")

    symptom_list = summary_row.summary_content.get("symptoms",[])

    patient_name = "patient"
    if session.appointment and session.appointment.user:
        patient_name = session.appointment.user.full_name

    #generate pdf
    report_dir = "reports"
    os.makedirs(report_dir, exist_ok=True)

    filename = f"symptom_report_{session_id}.pdf"
    file_path = os.path.join(report_dir, filename)
    generate_summary_pdf(session_id, patient_name, symptom_list, file_path)

    email_sent = send_report_email(file_path, patient_name, session_id)
    if not email_sent:
        print("Error sending email but pdf has been generated")

    session.ended_at=datetime.now()

    db.commit()
    return {"status": "success",
            "message": "Session finalized and PDF generated and sent to doctor",
            "pdf_path": file_path,
            "email_sent": email_sent}