from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import secrets

from backend.app.database import get_db
from backend.app import schemas,model
from backend.app.auth_security_dependencies import get_current_doctor
from backend.services.code_service import generate_access_code


router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.post("/", response_model=schemas.AppointmentResponse)
def create_appointments(
        payload:schemas.AppointmentCreate,
        db: Session = Depends(get_db),
        doctor: model.Doctor = Depends(get_current_doctor)):
    access_code = generate_access_code()

    appointment = model.Appointment(
        doctor_id=doctor.id,
        appointment_date=payload.appointment_date,
        access_code=access_code,
        status="scheduled"
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment