# RecoverAI Local Development Setup Guide

Follow these steps to set up and run RecoverAI locally on your machine.

---

## Prerequisites
- **Python**: 3.10 or higher
- **Node.js**: 18.x or higher (with npm)
- **PostgreSQL** (Optional for day 1; SQLite fallback is built-in)

---

## 1. Environment Configuration

Copy `.env.example` to `.env` in the root directory:

```bash
cp .env.example .env
```

Edit `.env` to supply your OpenAI API key or Razorpay test credentials when ready.

---

## 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations (optional, tables auto-create in dev)
alembic -c ../database/alembic.ini upgrade head

# Start FastAPI server
python run.py
```

Backend will be accessible at:
- Server: [http://localhost:8000](http://localhost:8000)
- Swagger UI Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 3. Frontend Setup

In a new terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Next.js development server
npm run dev
```

Frontend will be accessible at:
- Web App: [http://localhost:3000](http://localhost:3000)
