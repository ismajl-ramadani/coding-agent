import sys
from session_manager import get_latest_session_id, load_session, save_session
import json

session_id = get_latest_session_id()
if not session_id:
    print("No session found.")
    sys.exit()

messages = load_session(session_id)
print("Loaded successfully!")
