# RecoverAI — Production Deployment Guide

This document outlines the step-by-step procedure for deploying **RecoverAI** to production-grade infrastructure:
- **Frontend:** Next.js on **Vercel**
- **Backend:** FastAPI on **Render**
- **Database:** Serverless PostgreSQL on **Neon**
- **Payment Gateway:** **Razorpay Test Mode**

---

## 1. Production Architecture Diagram

```
                              GitHub (LakshGarg17/RecoverAI)
                                      │
                 ┌────────────────────┴────────────────────┐
                 ▼                                         ▼
       Vercel (Next.js 14)                       Render (FastAPI)
  (https://recoverai.vercel.app)         (https://recoverai-api.onrender.com)
                 │                                         │
                 │   REST / JSON                           ├─────────────────────────┐
                 └─────────────────────────────────────────┤                         │
                                                           ▼                         ▼
                                                  Neon PostgreSQL           Razorpay Test Mode
                                              (ep-xyz.neon.tech/db)       (Payment Links & SDK)
                                                           ▲                         │
                                                           └──── Webhook Notification┘
                                                               (HMAC-SHA256 Signed)
```

---

## 2. Environment Variables Specification

### Backend (Render Web Service)

| Environment Variable | Type | Required | Description / Example |
| :--- | :---: | :---: | :--- |
| `ENVIRONMENT` | string | Yes | Set to `production` |
| `DEBUG` | boolean | Yes | Set to `false` |
| `PORT` | number | Auto | Render sets this automatically (e.g., `10000`) |
| `DATABASE_URL` | string | **Yes** | Neon PostgreSQL connection string (`postgresql://user:pass@ep-xyz.neon.tech/recoverai?sslmode=require`) |
| `USE_SQLITE_FALLBACK` | boolean | Yes | Set to `false` in production |
| `FRONTEND_URL` | string | **Yes** | Your deployed Vercel URL (e.g. `https://recoverai.vercel.app`) |
| `BACKEND_CORS_ORIGINS`| string | Optional | JSON array or comma-separated list of origins (e.g. `["https://recoverai.vercel.app"]`) |
| `OPENAI_API_KEY` | string | **Yes** | OpenAI API Key (`sk-...`) for AI Diagnosis Agent |
| `OPENAI_MODEL` | string | Optional | Default `gpt-4o-mini` |
| `RAZORPAY_KEY_ID` | string | **Yes** | Razorpay Test Key ID (`rzp_test_...`) |
| `RAZORPAY_KEY_SECRET` | string | **Yes** | Razorpay Test Key Secret |
| `RAZORPAY_CURRENCY` | string | Optional | Default `INR` |
| `RAZORPAY_WEBHOOK_SECRET` | string | **Yes** | Webhook Secret for HMAC-SHA256 signature verification |

### Frontend (Vercel Project)

| Environment Variable | Type | Required | Description / Example |
| :--- | :---: | :---: | :--- |
| `NEXT_PUBLIC_API_URL` | string | **Yes** | Base URL of your deployed Render backend (e.g. `https://recoverai-backend.onrender.com`) |
| `NEXT_PUBLIC_APP_NAME` | string | Optional | `RecoverAI` |
| `NEXT_PUBLIC_RAZORPAY_KEY_ID` | string | Optional | Razorpay Test Key ID (`rzp_test_...`) |

---

## 3. Database Setup: Neon PostgreSQL

1. **Create Neon Project:**
   - Log into [Neon Console](https://console.neon.tech).
   - Click **New Project** $\rightarrow$ Name: `recoverai-prod` $\rightarrow$ Region: Choose closest to Render (e.g. `US East / Ohio` or `Singapore`).
2. **Copy Connection String:**
   - On the Neon Dashboard, copy the connection string:
     ```
     postgresql://<user>:<password>@<endpoint-id>.neon.tech/neondb?sslmode=require
     ```
3. **Run Alembic Migrations Against Neon:**
   - From your local development machine (or deployment CI), run:
     ```bash
     export DATABASE_URL="postgresql://<user>:<password>@<endpoint-id>.neon.tech/neondb?sslmode=require"
     alembic -c database/alembic.ini upgrade head
     ```
   - *Result:* Creates all tables (`customers`, `transactions`, `recovery_cases`, `recovery_decisions`, `guardrail_audit_logs`, `recovery_executions`, `recovery_records`).
4. **(Optional) Seed Demo Data:**
   - To populate initial merchant demo data into Neon:
     ```bash
     python database/seed.py
     ```

---

## 4. Backend Deployment: Render

### Option A: Via `render.yaml` (Blueprint)
1. Go to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** $\rightarrow$ **Blueprint**.
3. Select your repository (`LakshGarg17/RecoverAI`).
4. Render will detect `render.yaml`. Fill in the sync variables (`DATABASE_URL`, `OPENAI_API_KEY`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`, `FRONTEND_URL`).
5. Click **Apply**.

### Option B: Manual Web Service Setup
1. Click **New +** $\rightarrow$ **Web Service**.
2. Connect your GitHub repository: `LakshGarg17/RecoverAI`.
3. Configure settings:
   - **Name:** `recoverai-backend`
   - **Language:** `Python 3`
   - **Region:** Same as Neon (e.g. `Oregon` / `Ohio`)
   - **Branch:** `master` / `main`
   - **Root Directory:** *(leave blank / repo root)*
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
4. Under **Environment Variables**, add all required variables listed above.
5. Under **Health Check Path**, set `/health`.
6. Click **Create Web Service**. Note your Render URL (e.g., `https://recoverai-backend.onrender.com`).

---

## 5. Frontend Deployment: Vercel

1. Log into [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** $\rightarrow$ **Project**.
3. Import your GitHub repository: `LakshGarg17/RecoverAI`.
4. Configure project settings:
   - **Framework Preset:** `Next.js`
   - **Root Directory:** Click Edit $\rightarrow$ select `frontend`
   - **Build Command:** `next build` (default)
   - **Output Directory:** `.next` (default)
5. Under **Environment Variables**, add:
   - `NEXT_PUBLIC_API_URL` = `https://<your-render-backend-url>.onrender.com`
   - `NEXT_PUBLIC_APP_NAME` = `RecoverAI`
6. Click **Deploy**.
7. Note your Vercel deployment URL (e.g. `https://recoverai.vercel.app`).
8. **Update Backend CORS:** Return to your Render dashboard $\rightarrow$ set `FRONTEND_URL` = `https://recoverai.vercel.app` (or add to `BACKEND_CORS_ORIGINS`).

---

## 6. Razorpay Test Mode Webhook Setup

1. Log into your [Razorpay Dashboard](https://dashboard.razorpay.com).
2. Ensure top-left switch is in **Test Mode** (Amber badge).
3. Navigate to **Settings** $\rightarrow$ **Webhooks** $\rightarrow$ Click **+ Add New Webhook**.
4. Configure Webhook:
   - **Webhook URL:** `https://<your-render-backend-url>.onrender.com/api/webhooks/razorpay`
   - **Secret:** Enter a strong random secret (e.g., `whsec_recoverai_test_2026`) and copy this value to your Render `RAZORPAY_WEBHOOK_SECRET` environment variable.
   - **Active Events:**
     - `payment_link.paid`
     - `payment_link.cancelled`
     - `payment_link.expired`
     - `payment.captured`
     - `payment.failed`
5. Click **Create Webhook**.

---

## 7. Post-Deployment Verification Checklist

- [ ] **Health Check:** `curl -I https://<render-url>/health` returns `200 OK` with JSON `{ "status": "ok", "environment": "production" }`.
- [ ] **Swagger UI:** Open `https://<render-url>/docs` to verify OpenAPI schema is accessible.
- [ ] **Frontend Overview:** Open `https://<vercel-url>/` to confirm KPIs, Charts, and Recovery Funnel load live from backend.
- [ ] **AI Diagnosis Test:** Trigger a diagnosis on `/recovery` and inspect the structured recommendation.
- [ ] **Guardrails Enforcement:** Confirm Guardrails page shows active safety limits.
- [ ] **Webhook Simulation:** Trigger a test webhook from Razorpay Dashboard and confirm execution status updates in `/audit`.
