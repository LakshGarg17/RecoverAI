# RecoverAI — Day 10 Final Demo Guide & Judge Presentation

## 🚀 Executive Summary & Value Proposition

**RecoverAI** is an autonomous revenue recovery agent purpose-built for Indian e-commerce merchants. When high-intent shoppers encounter payment gateway drops, UPI session timeouts, or cart hesitations, RecoverAI diagnoses why the loss occurred, selects an optimal recovery action using Expected Value scoring, validates it against 10 strict merchant guardrails, and executes an approved recovery link via Razorpay Test Mode—reconciling recovered revenue into an immutable ledger upon webhook arrival.

---

## ⏱️ 60–90 Second Narrated Demo Script

| Timing | Phase | Script & Narration | Visual Focus on Screen |
|---|---|---|---|
| **0:00 – 0:10** | **The Problem** | *"Indian e-commerce loses up to 70% of checkout value to cart abandonment and transient UPI or gateway drops. Traditional tools blast generic spam hours later, causing high customer fatigue and low conversion."* | Main Executive Dashboard (`http://localhost:3000`) |
| **0:10 – 0:20** | **The Dashboard** | *"RecoverAI continuously monitors revenue at risk. On our executive dashboard, merchants see real-time KPIs: ₹45.2 Lakhs monitored, ₹9.18 Lakhs recovered, a 20.3% recovery rate, and our 14-day dunning trend."* | KPI Cards & 14-Day Recovery Trend Chart |
| **0:20 – 0:35** | **AI Diagnosis & EV** | *"Let's drill into opportunity `EVT-0042`—a ₹4,800 cart. Our multi-signal risk engine scores it 92/100 for high intent. GPT-4o-mini diagnoses a technical UPI timeout and drafts an empathetic recovery outreach, while our Decision Engine selects a `PAYMENT_LINK` based on Expected Value."* | Opportunity Detail Drawer (`/recovery/[id]`) |
| **0:35 – 0:45** | **Bounded Guardrails** | *"Crucially, AI never calls payments directly. Before execution, our Guardrail Engine evaluates 10 strict deterministic checks—enforcing quiet hours, 120-minute cooldowns, contact frequency limits, and transaction caps."* | 10 Guardrail Safety Checks Table (All `PASSED`) |
| **0:45 – 0:60** | **Razorpay Test Mode** | *"With guardrails approved, the merchant or agent dispatches recovery. RecoverAI calls Razorpay Test Mode API to generate an instant, pre-filled checkout link (`https://rzp.io/i/...`)."* | Razorpay Payment Link preview & Click to open |
| **0:60 – 0:70** | **Webhook Reconciliation** | *"When the customer pays in Test Mode, Razorpay fires a webhook. RecoverAI cryptographically verifies the HMAC-SHA256 signature, updates the case to `RECOVERED`, and logs an immutable entry in the recovery ledger."* | Webhook Event & StatusBadge updating to `RECOVERED` |
| **0:70 – 0:90** | **Proof of ROI & Impact** | *"On our AI Insights page, merchants inspect unit economics: at ₹0.65 operating cost per attempt, RecoverAI delivered ₹9.18 Lakhs in recovered revenue—a 16.9x lift over the organic baseline with a 28.5% AI action success rate."* | AI Insights & ROI Page (`/ai-insights`) |

---

## 🎯 Three Core Selling Points

### 1. Actionable Recovery Workflow, Not Just Prediction
Unlike passive analytics tools that merely flag churned carts or display post-facto charts, RecoverAI executes an end-to-end recovery pipeline: from behavioral detection and root-cause diagnosis to instant payment link creation and ledger reconciliation.

### 2. Bounded AI Autonomy with 10 Merchant Guardrails
AI is leveraged where it excels (contextual diagnosis, intent understanding, and personalized messaging), but deterministic code governs where safety is mandatory. The AI agent has zero direct gateway credentials; 10 deterministic merchant guardrails prevent customer spam, enforce quiet cooldowns, and eliminate duplicate charges.

### 3. Transparent, Measurable Revenue Impact
Every recovery metric is traceable: Revenue at Risk, Recovered Revenue, AI Action Success Rate, per-action conversion benchmarks, and ROI unit economics are computed directly from the PostgreSQL/SQLite database and verified through cryptographic webhooks.

---

## 🖱️ Step-by-Step Click-by-Click Demo Walkthrough

### Step 1: Open the Executive Dashboard
- **Action**: Navigate to `http://localhost:3000`.
- **What to Highlight**:
  - **4 Top KPI Cards**: Revenue at Risk (₹45.2L), Recovered Revenue (₹9.18L), Recovery Rate (20.32%), Active Cases (120).
  - **14-Day Recovery Trend**: Visual comparison of daily revenue dropped vs. recovered.
  - **5-Stage Conversion Funnel**: Drop-off progression from Identified $\rightarrow$ Scored $\rightarrow$ Diagnosed $\rightarrow$ Guardrail Approved $\rightarrow$ Reconciled.

### Step 2: Explore Recovery Opportunities
- **Action**: Click on **"Recovery Opportunities"** in the sidebar (`/recovery`).
- **What to Highlight**:
  - Filter by Priority Tier (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
  - Search by Customer ID or Event ID.
  - Note how opportunities are prioritized by Expected Value rather than chronological order.

### Step 3: Inspect Case Detail & AI Explainability
- **Action**: Click on high-priority case (e.g. `evt_e2e_...` or a curated demo case).
- **What to Highlight**:
  - **Behavioral Intent Breakdown**: Cart size, prior orders, session duration, page views.
  - **Clinical AI Diagnosis**: Root-cause explanation (e.g. *UPI Gateway Timeout during flash checkout*).
  - **Drafted Outreach**: Contextual customer message drafted by GPT-4o-mini.

### Step 4: Review the 10 Guardrail Safety Checks
- **Action**: Scroll to the **"Guardrail Safety & Policy Rules"** table on the detail page.
- **What to Highlight**:
  - Point out that all 10 checks are verified:
    1. Purchase Completion (not completed)
    2. Risk Threshold ($\ge 30.0$)
    3. Recovery Probability ($\ge 15\%$)
    4. Expected Value ($\ge ₹50.00$)
    5. Max Attempts ($< 3$)
    6. Cooldown Window ($\ge 120$ mins)
    7. Duplicate Action Check (Unique)
    8. Action Permission (Merchant flag enabled)
    9. Transaction Limit ($\le ₹50,000$)
    10. Customer Contact Frequency ($< 2$ / 24h)

### Step 5: Execute Recovery & Generate Razorpay Link
- **Action**: Click **"Dispatch Recovery"**.
- **What to Highlight**:
  - Pre-execution check runs to confirm real-time cart state.
  - Razorpay Test Mode Payment Link is generated (`https://rzp.io/i/...`).
  - Payment link and short URL appear immediately on the interface.

### Step 6: Verify Webhook Signature & Ledger Reconciliation
- **Action**: Open the payment link in Test Mode or observe the simulated webhook payload.
- **What to Highlight**:
  - The webhook arrives at `POST /api/webhooks/razorpay`.
  - HMAC-SHA256 signature is verified using the configured webhook secret.
  - Status updates instantly to `RECOVERED` in the database.

### Step 7: Inspect Proof of Recovery & ROI Analytics
- **Action**: Navigate to **"AI Insights"** (`/ai-insights`).
- **What to Highlight**:
  - **Unit Economics Card**: ₹0.65 operating cost vs. ₹9.18L gross recovered revenue.
  - **Simulated Baseline Comparison**: 1.20% organic return rate vs. 20.32% RecoverAI rate (+19.12% lift).
  - **Action Performance Table**: Highest conversion in `PAYMENT_LINK` (37.65%) and `PERSONALIZED_REMINDER` (28.05%).
  - **Risk Calibration Table**: Proves that carts with intent score 81–100 converted 6.8x higher than low-intent carts.

---

## 🧑‍⚖️ Comprehensive Judge Q&A Preparation

### Q1: "Why use AI instead of static rule-based drip campaigns?"
> **Answer**: Static drip campaigns treat all drops identically—sending generic emails 24 hours later regardless of whether a customer experienced a transient UPI timeout or was casually price-browsing. RecoverAI uses AI to diagnose the specific root cause and draft calibrated messaging, while using deterministic Expected Value scoring to prioritize high-intent cases.

### Q2: "Can the AI agent hallucinate discounts or directly make unauthorized payments?"
> **Answer**: **No.** RecoverAI enforces **Bounded Autonomy**. The AI model only produces structured diagnostic reasoning and drafted text. It has zero payment credentials or direct gateway access. Deterministic code selects the action, 10 merchant guardrails validate safety, and only the isolated Execution Engine can invoke the Razorpay API.

### Q3: "Why did you choose Razorpay?"
> **Answer**: Razorpay is the leading payment gateway for Indian e-commerce, offering native UPI deep-linking, automated payment links, robust webhook callbacks, and a comprehensive Test Mode environment that mirrors production transaction lifecycles.

### Q4: "How do you prevent customer fatigue and spam?"
> **Answer**: We implement 3 specific anti-fatigue guardrails in code:
> 1. **Attempt Cap**: Maximum 3 recovery attempts per case.
> 2. **Cooldown Window**: Mandatory 120-minute quiet window between contacts.
> 3. **Contact Frequency Limit**: Maximum 2 interventions per customer across a rolling 24-hour window.

### Q5: "Is the ₹9.18 Lakhs recovery number real, and how is it evaluated?"
> **Answer**: The evaluation is run across 25,000 real transaction sessions from a benchmark Indian e-commerce Kaggle dataset. Recoveries are executed against Razorpay Test Mode with full HMAC-verified webhook reconciliation. Because this is a benchmark evaluation rather than a live randomized control trial on live production traffic, we explicitly label the organic baseline as **Simulated Baseline** and incremental lift as **Estimated Incremental Recovery**.

### Q6: "How do you handle duplicate execution requests or duplicate webhooks?"
> **Answer**: Both the Execution Engine and Webhook Controller implement **Idempotency Keys**. If a merchant or agent triggers execution twice, the system returns the existing payment link without creating a duplicate. If Razorpay retries a webhook, the payload signature is verified and processed once; duplicate deliveries are acknowledged as no-ops.

---

## 🔒 Security & Invariants Checklist

- [x] **No Secrets in Repo**: All API keys and secrets stored in `.env` (untracked).
- [x] **Fail-Closed Architecture**: Missing risk score or unverified cart state automatically halts execution.
- [x] **Cryptographic Webhook Validation**: HMAC-SHA256 verification using constant-time digest comparison (`hmac.compare_digest`).
- [x] **Test Mode Exclusivity**: Operates strictly against `rzp_test_...` credentials.
- [x] **Tamper-Evident Dual Audit**: All decisions, guardrail checks, and executions logged in database tables (`guardrail_audit_logs`, `recovery_executions`, `recovery_records`).
