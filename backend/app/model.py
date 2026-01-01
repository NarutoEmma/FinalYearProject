from sqlalchemy import (Column,
                        Integer,
                        String,
                        ForeignKey,
                        Text,
                        DateTime,
                        Enum,
                        JSON,
                        Index)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.app.database import Base,engine


class Doctor(Base):
    __tablename__ = 'doctors'
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email=Column(String(100), unique=True, nullable=False)
    password_hash=Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    appointments = relationship("Appointment", back_populates="doctor")

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100))
    email=Column(String(100), unique=True)
    appointments = relationship("Appointment", back_populates="user")
    created_at = Column(DateTime, server_default=func.now())

class Appointment(Base):
    __tablename__ = 'appointments'
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    appointment_date = Column(DateTime, nullable=False)
    access_code= Column(String(8), unique=True, nullable= False, index=True)
    code_used_at = Column(DateTime, nullable = True)
    status = Column(
        Enum("scheduled", "in_progress", "completed", "cancelled", name="appointment_status"),
        default="scheduled", nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    doctor = relationship("Doctor", back_populates="appointments")
    user = relationship("User", back_populates="appointments")
    sessions = relationship("Session", back_populates="appointment", uselist=False)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)

    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime, nullable=True)

    appointment = relationship("Appointment", back_populates="sessions")
    messages = relationship("Message", back_populates="session")
    summary = relationship("Summary", back_populates="session", uselist=False)

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)

    sender = Column(
        Enum("user", "ai", name="message_sender"),
        nullable=False
    )
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    session = relationship("Session", back_populates="messages")

class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), unique=True, nullable=False)

    summary_content = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    session = relationship("Session", back_populates="summary")