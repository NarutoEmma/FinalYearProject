# routes/reports.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime

from pdf_generator import generate_summary_pdf
from session_manager import (
    get_session,
    complete_session,
    update_session_symptoms,
    create_session
)

router = APIRouter(prefix="/api/reports", tags=["reports"])

# Request models
class Symptom(BaseModel):
    symptom: str
    severity: Optional[str] = "Not specified"
    duration: Optional[str] = "Not specified"
    frequency: Optional[str] = "Not specified"

class CompleteSessionRequest(BaseModel):
    session_id: int
    patient_name: str
    symptoms: List[Symptom]

# ==================== ENDPOINTS ====================

@router.post("/complete-session")
async def complete_patient_session(request: CompleteSessionRequest):
    """
    Complete a session and generate PDF report

    This is called when user clicks "Complete Session" in the app
    """
    try:
        # 1. Validate session exists (or create if first time)
        session = get_session(request.session_id)
        if not session:
            # Create session if it doesn't exist
            session = create_session(request.session_id, request.patient_name)

        # 2. Update symptoms
        symptoms_list = [s.dict() for s in request.symptoms]
        update_session_symptoms(request.session_id, symptoms_list)

        # 3. Generate PDF
        os.makedirs("reports", exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = f"reports/patient_report_{request.session_id}_{timestamp}.pdf"

        pdf_path = generate_summary_pdf(
            session_id=request.session_id,
            patient_name=request.patient_name,
            symptoms=symptoms_list,
            file_path=file_path
        )

        # 4. Mark session as completed
        completed_session = complete_session(request.session_id, pdf_path)

        # 5. Return success
        return {
            "success": True,
            "message": "Session completed and report generated successfully",
            "session_id": request.session_id,
            "report_path": pdf_path,
            "session": completed_session
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete session: {str(e)}"
        )


@router.get("/download/{session_id}")
async def download_report(session_id: int):
    """
    Download the PDF report for a completed session
    """
    session = get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session["status"] != "completed":
        raise HTTPException(status_code=400, detail="Session not completed yet")

    report_path = session.get("report_path")

    if not report_path or not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report file not found")

    return FileResponse(
        report_path,
        media_type="application/pdf",
        filename=f"patient_report_{session_id}.pdf"
    )


@router.get("/session/{session_id}")
async def get_session_info(session_id: int):
    """
    Get information about a session
    """
    session = get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@router.get("/completed-sessions")
async def get_completed_sessions():
    """
    Get all completed sessions (for doctor dashboard)
    """
    from session_manager import get_all_completed_sessions
    return {
        "sessions": get_all_completed_sessions()
    }