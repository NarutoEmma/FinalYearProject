from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime

from starlette.status import HTTP_401_UNAUTHORIZED

from backend.app.database import get_db
from backend.app import model,schemas
from backend.services.auth_service import (
get_password_hash, verify_password, create_access_token
)



router = APIRouter()
#register doctor
@router.post("/register", response_model=schemas.DoctorResponse)
def register_doctor(
        doctor: schemas.DoctorCreate,
        db: Session = Depends(get_db)):
    #check is doctor exists
    existing_doctor = db.query(model.Doctor).filter(
        model.Doctor.email == doctor.email).first()
    if existing_doctor:
        raise HTTPException(status_code=400,
                            detail="Email already registered")
    #create doctor
    new_doctor = model.Doctor(
        full_name=doctor.full_name,
        email=doctor.email,
        password_hash=get_password_hash(doctor.password))
    db.add(new_doctor)
    db.commit()
    db.refresh(new_doctor)
    return {"id":new_doctor.id, "full_name":new_doctor.full_name,
            "email": new_doctor.email}

#login doctor
@router.post("/login", response_model=schemas.Token)
def login_doctor(
        form_data: OAuth2PasswordRequestForm=Depends(),
        db: Session = Depends(get_db)):
    doctor = db.query(model.Doctor).filter(
        model.Doctor.email == form_data.username).first()
    if not doctor or not verify_password(form_data.password, doctor.password_hash):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    token = create_access_token({"sub": str(doctor.id)})
    return {"access_token": token, "token_type": "bearer"}




