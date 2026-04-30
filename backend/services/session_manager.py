# backend/services/session_manager.py
import sys
from pathlib import Path

#add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()  # load DB credentials

from backend.app.database import SessionLocal
from backend.app.model import Session, Appointment

def check_session(session_id: int):
    db = SessionLocal()

    print("=" * 60)
    print(f"CHECKING SESSION {session_id}")
    print("=" * 60)

    try:
        session = db.query(Session).filter(Session.id == session_id).first()

        if not session:
            print(f"❌ Session {session_id} not found in database!")
            return

        print(f"\n📋 Session Details:")
        print(f"   ID: {session.id}")
        print(f"   Appointment ID: {session.appointment_id}")
        print(f"   Started At: {session.started_at}")
        print(f"   Ended At: {session.ended_at}")

        if session.ended_at:
            print(f"\n✅ SESSION HAS ENDED!")
            duration = session.ended_at - session.started_at
            print(f"   Duration: {duration}")
        else:
            print(f"\n⚠️ SESSION IS STILL ACTIVE (not ended)")

        # Check appointment status
        if session.appointment:
            appointment = session.appointment
            print(f"\n📅 Appointment Details:")
            print(f"   ID: {appointment.id}")
            print(f"   Status: {appointment.status}")
            print(f"   Access Code: {appointment.access_code}")

            if appointment.status == "completed":
                print(f"   ✅ Appointment marked as COMPLETED")
            elif appointment.status == "in_progress":
                print(f"   ⚠️ Appointment still IN PROGRESS")
            else:
                print(f"   Status: {appointment.status}")

        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nCheck:")
        print("  1. MySQL is running (XAMPP/MySQL service)")
        print("  2. .env file exists with correct DB credentials")
        print("  3. Database 'preconsultationdb' exists")

    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        session_id = int(sys.argv[1])
    else:
        session_id = int(input("Enter session ID to check: "))

    check_session(session_id)