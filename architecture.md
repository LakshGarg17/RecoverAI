# RecoverAI Architecture Specification

## High-Level Architecture Overview

RecoverAI is an autonomous payment recovery engine designed to recover overdue and failed B2B / SaaS subscription payments using calibrated AI dunning workflows and automated payment orchestration.

```
┌────────────────────────────────────────────────────────┐
│               Frontend (Next.js 14+)                   │
│   Tailwind CSS • Recharts • Live Agent Dashboard       │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTP / JSON API
                           ▼
┌────────────────────────────────────────────────────────┐
│               FastAPI Gateway (backend/)               │
│   - CORS Middleware      - Versioned Routing (/api/v1) │
│   - Pydantic Validation  - Health & Diagnostics API    │
└────────────┬─────────────────────┬───────────────────┬─┘
             │                     │                   │
             ▼                     ▼                   ▼
┌──────────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Database Layer       │ │ AI Agent Engine  │ │ Payments Gateway │
│ PostgreSQL + Alembic │ │ OpenAI API       │ │ Razorpay SDK     │
│ (SQLite Dev Fallback)│ │ (Structured JSON)│ │ (Test Mode)      │
└──────────────────────┘ └──────────────────┘ └──────────────────┘
```

## Core Subsystems

### 1. Frontend (`frontend/`)
- Built on **Next.js App Router** with TypeScript.
- **Tailwind CSS** for rich modern UI styling (dark mode, glassmorphism, accent badges).
- **Recharts** for real-time recovery analytics and metric visualizations.
- Centralized API consumer (`src/lib/api.ts`).

### 2. Backend Gateway (`backend/`)
- Powered by **FastAPI** with async execution and Pydantic v2 settings.
- Modular route handlers structured under `app/api/v1/endpoints/`.
- Dependency injection for database sessions (`get_db`).

### 3. Database Layer (`database/` & `backend/app/core/db.py`)
- **SQLAlchemy 2.0** ORM declarative models.
- **Alembic** schema migrations.
- Primary database target: PostgreSQL (Supabase / Neon / Render).
- Zero-config SQLite fallback for local dev when Postgres is offline.

### 4. AI Engine (`ai/` & `backend/app/services/ai_agent.py`)
- Structured JSON outputs via **OpenAI Chat Completions**.
- Dynamic risk assessment based on invoice age, communication history, and customer profile.

### 5. Payment Gateway (`backend/app/services/payments.py`)
- **Razorpay SDK** integration with test-mode simulation.
- Order creation and webhook/signature verification helpers.
