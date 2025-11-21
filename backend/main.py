from fastapi import FastAPI
from backend.database import engine
import model

model.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Backend + Database Connected"}