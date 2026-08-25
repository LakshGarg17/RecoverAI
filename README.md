# RecoverAI — Autonomous Payment Recovery Agent

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2%2B-black.svg)](https://nextjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4%2B-38B2AC.svg)](https://tailwindcss.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-red.svg)](https://www.sqlalchemy.org/)
[![Alembic](https://img.shields.io/badge/Alembic-1.13%2B-orange.svg)](https://alembic.sqlalchemy.org/)
[![Razorpay](https://img.shields.io/badge/Razorpay-Test%20Mode-0C2340.svg)](https://razorpay.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991.svg)](https://openai.com/)

**RecoverAI** is an autonomous agent designed to identify delinquent or failed SaaS subscriptions and B2B invoices, evaluate recovery likelihood with calibrated LLM agents, and execute empathetic multi-channel dunning with instant Razorpay checkout links.

---

## 🏗️ Architecture & Project Layout

```text
RecoverAI-Autonomous Payment Recovery Agent/
├── .env.example              # Centralized environment variable template
├── README.md                 # Complete documentation and setup guide
│
├── frontend/                 # Next.js 14 App Router + Tailwind CSS + Recharts
│   ├── src/
│   │   ├── app/              # App router pages, layout, and global styles
│   │   ├── components/       # UI components (Health diagnostics, Charts, Navbar)
│   │   └── lib/              # Centralized API client (`api.ts`) and TypeScript types
│   ├── package.json
│   ├── tailwind.config.js
│   └── tsconfig.json
│
├── backend/                  # FastAPI Python Application
│   ├── app/
│   │   ├── api/v1/           # Versioned API routes (/health, /payments, /ai)
│   │   ├── core/             # Configuration (pydantic-settings) and DB engine
│   │   ├── models/           # SQLAlchemy ORM declarative models (User, RecoveryCase)
│   │   ├── schemas/          # Pydantic validation schemas
│   │   ├── services/         # Razorpay SDK and OpenAI client services
│   │   └── main.py           # FastAPI entrypoint with CORS and lifespans
│   ├── run.py                # CLI server runner
│   └── requirements.txt      # Python dependencies
│
├── database/                 # Database migrations and Session bridge
│   ├── alembic/              # Migration scripts and environment configuration
│   ├── alembic.ini
│   ├── session.py            # Reusable database session adapter
│   └── README.md
│
├── ai/                       # AI Agent Prompt Engineering & Schemas
│   ├── client.py             # OpenAI Structured Outputs wrapper
│   ├── prompts/              # System prompt templates
│   └── schemas/              # Structured recovery decision schemas
│
├── tests/                    # Backend automated tests
│   ├── conftest.py           # Pytest TestClient fixture
│   ├── test_health.py        # API endpoint tests
│   └── test_db.py            # Database model tests
│
└── docs/                     # Comprehensive Architecture & API Documentation
    ├── architecture.md       # Detailed technical design specification
    ├── api_spec.md           # REST API endpoints & JSON payloads
    └── setup_guide.md        # Step-by-step developer guide
```

---

## ⚡ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | Next.js 14 (App Router) + TypeScript | Modern responsive web app & dashboard |
| **Styling** | Tailwind CSS + Lucide Icons | Dark mode, glassmorphism, responsive UI |
| **Charts** | Recharts | Dunning curves and risk segmentation analytics |
| **Backend** | FastAPI (Python 3.10+) | High-performance asynchronous REST API |
| **Database** | PostgreSQL + SQLAlchemy 2.0 | Persistent transactional storage (Supabase/Neon ready) |
| **Migrations** | Alembic | Version-controlled schema migrations |
| **AI Decisions** | OpenAI API (`gpt-4o-mini`) | Structured JSON dunning & tone calibration |
| **Payments** | Razorpay Python SDK | Test Mode order creation and payment links |

---

## 🚀 Quickstart & Local Setup

### 1. Configure Environment Variables
Copy `.env.example` to `.env` in the project root:

```bash
# Windows PowerShell
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

*(Optional)* Provide your real `OPENAI_API_KEY` and `RAZORPAY_KEY_ID` in `.env` if testing live integrations. Otherwise, the mock test mode will work out of the box.

---

### 2. Backend Setup & Run

Open a terminal and navigate to `backend/`:

```bash
cd backend

# 1. Create a virtual environment
python -m venv venv

# 2. Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
# source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. (Optional) Run database migrations
alembic -c ../database/alembic.ini upgrade head

# 5. Start the FastAPI server
python run.py
```

- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check Endpoint**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

### 3. Frontend Setup & Run

Open a second terminal and navigate to `frontend/`:

```bash
cd frontend

# 1. Install Node dependencies
npm install

# 2. Start the development server
npm run dev
```

- **Frontend Web App**: [http://localhost:3000](http://localhost:3000)

Once both servers are running, the frontend dashboard will automatically connect to `http://localhost:8000/api/health` and display real-time latency and service diagnostics.

---

## 🧪 Running Tests

Execute backend automated tests from the repository root:

```bash
pytest tests/ -v
```

---

## 🚢 Deployment Targets

- **Frontend**: [Vercel](https://vercel.com/)
- **Backend**: [Render](https://render.com/) or [Railway](https://railway.app/)
- **Database**: [Supabase](https://supabase.com/) or [Neon](https://neon.tech/) (PostgreSQL)

---

## 📜 License
MIT License. Built for autonomous revenue recovery.
