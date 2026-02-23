from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app import model, schemas
from backend.routers import sessions, appointments, auth
from backend.services.ai_service import generate_ai_response

router = APIRouter(tags=["Chat"])

# ✅ NEW: Get chat history endpoint
@router.get("/{session_id}/history")
def get_chat_history(session_id: int, db: Session = Depends(get_db)):
    """
    Get all previous chat messages for a session
    """
    # Validate session exists
    session = db.query(model.Session).filter(
        model.Session.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get all messages for this session
    messages = db.query(model.Message).filter(
        model.Message.session_id == session_id
    ).order_by(model.Message.created_at.asc()).all()

    # Format for frontend
    chat_history = []
    for msg in messages:
        chat_history.append({
            "id": str(msg.id),
            "role": msg.sender,  # "user" or "ai"
            "text": msg.content,
            "timestamp": msg.created_at.isoformat()
        })

    print(f"📜 Retrieved {len(chat_history)} messages for session {session_id}")

    return {
        "session_id": session_id,
        "message_count": len(chat_history),
        "messages": chat_history
    }


@router.post("/{session_id}", response_model=schemas.ChatResponse)
def chat_with_ai(
        session_id: int,
        payload: schemas.MessageCreate,
        db: Session = Depends(get_db)
):
    # Validate session
    session = db.query(model.Session).filter(
        model.Session.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Invalid session id")

    existing_summary_row = db.query(model.Summary).filter(
        model.Summary.session_id == session_id
    ).first()
    current_state = existing_summary_row.summary_content if existing_summary_row else None

    # Save user message
    user_message = model.Message(
        session_id=session_id,
        sender="user",
        content=payload.content
    )
    db.add(user_message)
    db.commit()

    messages = db.query(model.Message).filter(
        model.Message.session_id == session_id
    ).order_by(model.Message.created_at).all()

    # Build chat history from db
    chat_history = [
        {
            "role": "assistant" if m.sender == "ai" else "user",
            "content": m.content
        }
        for m in messages
    ]

    # Call AI
    ai_response = generate_ai_response(chat_history, current_state)
    reply_content = ai_response.get("reply", "i'm listening")

    # Save AI reply
    ai_message = model.Message(
        session_id=session_id,
        sender="ai",
        content=reply_content
    )
    db.add(ai_message)

    # Update summary table if AI extracted symptoms
    if ai_response.get("extracted") and ai_response["extracted"].get("symptoms"):
        if existing_summary_row:
            existing_summary_row.summary_content = ai_response["extracted"]
        else:
            new_summary = model.Summary(
                session_id=session_id,
                summary_content=ai_response["extracted"]
            )
            db.add(new_summary)
    db.commit()

    return ai_response