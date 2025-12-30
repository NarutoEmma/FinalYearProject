from fastapi import FastAPI
from backend.app.database import Base,engine
from backend.routers import auth, sessions, appointments,chat

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Pre-Consultation AI")

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
app.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])

@app.get("/")
def read_root():
    return {"status": "Backend + Database Connected"}