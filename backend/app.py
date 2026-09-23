"""
Course Enrollment Chatbot - Backend Application Entrypoint
Run using: python app.py
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Load environment variables
load_dotenv(dotenv_path=backend_dir / ".env")

import uvicorn
from main import app

if __name__ == "__main__":
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    
    print(f"[STARTING] Course Enrollment API backend server on http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)
