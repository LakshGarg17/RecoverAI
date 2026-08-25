# RecoverAI REST API Specification

All versioned endpoints are prefixed with `/api/v1`. Interactive Swagger documentation is available at `/docs`.

---

## Endpoints

### 1. Health Checks

#### `GET /api/health` (Top-level) & `GET /api/v1/health`
Checks backend responsiveness, database latency, and integration configurations.

**Response `200 OK`:**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "timestamp": "2026-08-24T22:30:00.000Z",
  "environment": "development",
  "services": {
    "database": {
      "status": "healthy",
      "latency_ms": 1.45,
      "details": { "engine": "postgresql" }
    },
    "razorpay": {
      "status": "configured",
      "details": { "mode": "live", "currency": "INR" }
    },
    "openai": {
      "status": "configured",
      "details": { "model": "gpt-4o-mini", "mode": "live" }
    },
    "backend": {
      "status": "healthy",
      "latency_ms": 0.5,
      "details": { "version": "0.1.0", "env": "development" }
    }
  }
}
```

---

### 2. Payments (Razorpay)

#### `POST /api/v1/payments/orders`
Create a payment order for invoice recovery.

**Request Body:**
```json
{
  "amount": 50000,
  "currency": "INR",
  "receipt": "rcpt_inv_1001",
  "notes": {
    "invoice_id": "INV-1001"
  }
}
```

**Response `200 OK`:**
```json
{
  "id": "order_mock_rcpt_inv_1001",
  "entity": "order",
  "amount": 50000,
  "amount_paid": 0,
  "amount_due": 50000,
  "currency": "INR",
  "receipt": "rcpt_inv_1001",
  "status": "created"
}
```

---

### 3. AI Agent (OpenAI)

#### `POST /api/v1/ai/analyze`
Analyze overdue invoice and generate autonomous communication draft.

**Request Body:**
```json
{
  "customer_name": "Globex Corp",
  "overdue_days": 14,
  "amount": 45000.0,
  "currency": "INR",
  "previous_communications": ["email_day_3"]
}
```

**Response `200 OK`:**
```json
{
  "risk_level": "low",
  "recommended_action": "friendly_reminder",
  "suggested_channel": "email",
  "personalized_draft": "Hi Globex Corp, this is a gentle reminder regarding invoice amount INR 45000.0...",
  "confidence_score": 0.95
}
```
