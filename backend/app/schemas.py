
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, Union, Any

#doctor schema
class DoctorBase(BaseModel):
    full_name: str
    email: EmailStr
class DoctorCreate(DoctorBase):
    password: str
class DoctorLogin(BaseModel):
    email: EmailStr
    password: str
class DoctorResponse(DoctorBase):
    id: int
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str="bearer"

#patients/users

class UserBase(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

#appointment
class AppointmentCreate(BaseModel):
    appointment_date: datetime

class AppointmentResponse(BaseModel):
    id: int
    doctor_id: int
    user_id: Optional[int]
    appointment_date : datetime
    access_code: str
    status: str
    created_at: datetime

    class Config:
        orm_mode = True

#session

class SessionCreate(BaseModel):
    access_code: str

class SessionResponse(BaseModel):
    id: int
    appointment_id: int
    message: str
    started_at: datetime
    ended_at: Optional[datetime]=None

    class Config:
        orm_mode = True

#messages
class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: int
    session_id: int
    sender: str
    content: str
    sent_message_at: datetime

    class Config:
        orm_mode = True

class SymptomInfo(BaseModel):
    symptom: Optional[str] = None
    duration: Optional[str] = None
    severity: Union[str, int, None] = None
    frequency: Union[str, int, None] = None

class ExtractedInfo(BaseModel):
    current_symptom_index: int
    symptoms: List[SymptomInfo]

#chat response
class ChatResponse(BaseModel):
    reply: str
    off_topic: bool
    extracted: ExtractedInfo

#summary
class SummaryResponse(BaseModel):
    id: int
    session_id: int
    summary_content: dict
    created_at: datetime

    class Config:
        orm_mode = True

