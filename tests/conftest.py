import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ensure backend is in python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.main import app
from app.core.config import settings


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
