import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from database.database import engine, SessionLocal, Base, get_db, init_db

__all__ = ["engine", "SessionLocal", "Base", "get_db", "init_db"]
