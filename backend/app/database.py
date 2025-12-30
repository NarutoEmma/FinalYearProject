from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "mysql+pymysql://root:Chinny.com123@localhost:3306/preconsultationdb"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # Prevents MySQL timeout issues
    pool_recycle=3600     # Recycles connections every hour
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
