import os
import json
import glob
from datetime import datetime
from google.genai import types

SESSIONS_DIR = ".sessions"

def ensure_sessions_dir():
    os.makedirs(SESSIONS_DIR, exist_ok=True)

def get_new_session_id() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"session_{timestamp}"

def get_latest_session_id() -> str | None:
    ensure_sessions_dir()
    files = glob.glob(os.path.join(SESSIONS_DIR, "session_*.json"))
    if not files:
        return None
    # Sort by modification time, newest first
    files.sort(key=os.path.getmtime, reverse=True)
    filename = os.path.basename(files[0])
    return filename[:-5] # remove .json

class BytesEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        return super().default(obj)

def save_session(session_id: str, messages: list[types.Content]):
    ensure_sessions_dir()
    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    
    serializable_messages = []
    for msg in messages:
        try:
            data = msg.model_dump(exclude_none=True, mode='json')
            serializable_messages.append(data)
        except Exception as e:
            print(f"Warning: Failed to serialize message: {e}")
            
    with open(filepath, "w", encoding="utf-8") as f:
        try:
            json.dump(serializable_messages, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print("Failed to save JSON:", e)
            print("Data:", serializable_messages)

def load_session(session_id: str) -> list[types.Content]:
    ensure_sessions_dir()
    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Session file not found: {filepath}")
        
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    messages = []
    for msg_data in data:
        messages.append(types.Content(**msg_data))
    return messages
