# cleanup_old_sessions.py
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from backend.app.database import SessionLocal
from backend.app.model import Session

def cleanup_sessions_range(start_id: int, end_id: int):
    """
    End all sessions in a specific ID range
    """
    db = SessionLocal()

    print("=" * 70)
    print(f"CLEANING UP SESSIONS {start_id} to {end_id}")
    print("=" * 70)

    ended_count = 0
    not_found_count = 0
    already_ended_count = 0

    for session_id in range(start_id, end_id + 1):
        session = db.query(Session).filter(Session.id == session_id).first()

        if not session:
            print(f"⚪ Session {session_id}: Not found (never existed)")
            not_found_count += 1
            continue

        if session.ended_at:
            print(f"⚪ Session {session_id}: Already ended at {session.ended_at}")
            already_ended_count += 1
            continue

        # End the session
        session.ended_at = datetime.now()

        # Update appointment status
        if session.appointment:
            session.appointment.status = "completed"

        print(f"✅ Session {session_id}: Ended (Appointment: {session.appointment_id if session.appointment else 'None'})")
        ended_count += 1

    # Commit all changes
    db.commit()
    db.close()

    print("\n" + "=" * 70)
    print("SUMMARY:")
    print(f"  ✅ Ended: {ended_count}")
    print(f"  ⚪ Already ended: {already_ended_count}")
    print(f"  ⚪ Not found: {not_found_count}")
    print(f"  📊 Total processed: {end_id - start_id + 1}")
    print("=" * 70)

if __name__ == "__main__":
    # End sessions 1-35
    cleanup_sessions_range(1, 35)