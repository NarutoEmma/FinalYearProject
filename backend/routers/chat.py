from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app import model,schemas
from backend.routers import sessions, appointments,auth
from backend.services.ai_service import generate_ai_response

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/{session_id}", response_model=schemas.ChatResponse)
def chat_with_ai(
        session_id:int,
        payload:schemas.MessageCreate,
        db: Session = Depends(get_db)
):
    #validate session
    session = db.query(model.Session).filter(
        model.Session.id==session_id).first()

    if not session:
        raise HTTPException(status_code=404, detail="Invalid session id")

    #save user message
    user_message = model.Message(session_id=session_id,
                            sender="user",
                            content=payload.content)
    db.add(user_message)
    db.commit()

    #build chat history from db
    messages = db.query(model.Message).filter(
        model.Message.session_id==session_id
    ).order_by(model.Message.created_at).all()

    chat_history= [
        {
            "role": "assistant" if m.sender=="ai" else "user",
            "content": m.content
        }
        for m in messages
    ]

    #call ai
    ai_response = generate_ai_response(chat_history)

    #save ai reply
    ai_message = model.Message(session_id=session_id,
                               sender="ai",
                               content=ai_response["reply"])
    db.add(ai_message)
    db.commit()

    return ai_response