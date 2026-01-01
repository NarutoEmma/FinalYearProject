#validate access code, create session and prevent multiple sessions
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from backend.app.database import get_db
from backend.app import schemas, model

router = APIRouter(prefix="/sessions", tags=["sessions"])

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
