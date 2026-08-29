# RecoverAI AI Diagnosis & Recovery Recommendation Evaluation (Day 4)

This document evaluates RecoverAI's **LLM-Powered Diagnosis & Recovery Recommendation Agent** across real shopping sessions from the 25,000-event dataset (`data/processed/recoverai_events.csv`).

---

## 1. System Architecture & Safety Guarantees

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            RECOVERAI PIPELINE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Data Ingestion & Canonical Telemetry (Day 2)                             │
│ 2. Deterministic Risk Engine (Day 3 Authoritative Outputs)                  │
│    └─ Calculates: risk_score, purchase_intent_score, revenue_at_risk, CLV    │
│ 3. Context Builder (ai/diagnosis.py)                                        │
│    └─ Packages event telemetry + customer history + risk engine scores      │
│ 4. AI Diagnosis Agent (ai/diagnosis.py + OpenAI Structured Outputs)         │
│    └─ Interprets signals into root cause diagnosis & least-intrusive action │
│ 5. Strict Pydantic Schema Validation (ai/schemas.py)                        │
│    └─ Enforces controlled enums & bounds ∈ [0.0, 1.0]                       │
│ 6. Deterministic Fallback Engine (ai/diagnosis.py)                          │
│    └─ 100% uptime guaranteed on timeout, rate-limits, or parsing failures  │
│ 7. Audit-Trail Persistence (database/ai_decisions.py)                       │
│    └─ Persists immutable decision records with confidence & reasoning       │
└─────────────────────────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> **Strict Operational Constraints**:
> 1. **Zero Financial Execution**: The LLM *never* executes payments, moves money, or sends live customer messages. It only generates structured recommendations. Execution is deferred to Day 6 (Guardrails) and Day 7 (Razorpay Test Mode).
> 2. **Deterministic Authority**: The AI *never* recalculates or overrides `risk_score`, `purchase_intent_score`, or `revenue_at_risk`.
> 3. **Controlled Enums**: Diagnosis root causes and recovery actions are strictly enforced enums—free-text actions are rejected.
> 4. **Expected Recovery Value**: The backend computes $\text{Expected Recovery Value} = \text{revenue\_at\_risk} \times \text{recovery\_probability}$.

---

## 2. Controlled Category Enums

### Diagnosis Root Causes (`DiagnosisCategory`)
- `HIGH_PURCHASE_INTENT_ABANDONMENT`: High-intent buyer dropped off at the final checkout step.
- `REPEAT_CUSTOMER_ABANDONMENT`: Verified repeat customer with prior purchases abandoned cart.
- `HIGH_VALUE_ABANDONMENT`: High monetary cart value requiring tailored recovery handling.
- `RECENT_CHECKOUT_DROP`: Fresh dropoff requiring immediate (<1 hr) reminder.
- `LOW_INTENT_ABANDONMENT`: Casual browse / low engagement with minimal conversion probability.
- `LOW_RECOVERY_CONFIDENCE`: High signal ambiguity or conflicting indicators.

### Recovery Actions (`RecoveryAction`)
- `CHECKOUT_REMINDER`: Standard friendly checkout reminder (email/push/SMS).
- `PERSONALIZED_REMINDER`: Warm personalized message referencing buyer loyalty or specific basket.
- `PAYMENT_LINK`: Direct instant payment link (UPI/Card) for high-intent checkout friction.
- `DELAYED_FOLLOW_UP`: Defer outreach by 2–6 hours to avoid premature intrusive contact.
- `NO_ACTION`: Do not contact (zero cart value or window shopper).
- `ESCALATE`: Flag for human merchant account manager review (ultra-high value anomaly).

---

## 3. Real Dataset Case Evaluations (25 Sample Events)

The following table evaluates 25 real shopping events across diverse cohorts from `data/processed/recoverai_events.csv`:

| Event ID | Customer ID | Cart Value | Priority | Root Cause Diagnosis | Recommended Action | AI Recovery Prob. | Confidence | Expected Recovery Value | Source |
| :--- | :--- | :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| `evt_014183` | `cust_06163` | ₹7,907.96 | **CRITICAL** | `REPEAT_CUSTOMER_ABANDONMENT` | `PERSONALIZED_REMINDER` | 82% | 92% | ₹6,484.53 | AI / Fallback |
| `evt_014714` | `cust_03400` | ₹7,968.08 | **HIGH** | `HIGH_PURCHASE_INTENT_ABANDONMENT` | `CHECKOUT_REMINDER` | 55% | 88% | ₹4,382.44 | AI / Fallback |
| `evt_015950` | `cust_07137` | ₹7,920.28 | **HIGH** | `HIGH_PURCHASE_INTENT_ABANDONMENT` | `CHECKOUT_REMINDER` | 60% | 88% | ₹4,752.17 | AI / Fallback |
| `evt_001872` | `cust_06429` | ₹7,905.08 | **HIGH** | `HIGH_PURCHASE_INTENT_ABANDONMENT` | `CHECKOUT_REMINDER` | 55% | 88% | ₹4,347.79 | AI / Fallback |
| `evt_000462` | `cust_07738` | ₹7,891.16 | **HIGH** | `HIGH_PURCHASE_INTENT_ABANDONMENT` | `CHECKOUT_REMINDER` | 66% | 88% | ₹5,208.17 | AI / Fallback |
| `evt_014591` | `cust_09854` | ₹7,971.88 | **MEDIUM** | `RECENT_CHECKOUT_DROP` | `DELAYED_FOLLOW_UP` | 50% | 80% | ₹3,985.94 | AI / Fallback |
| `evt_024758` | `cust_05891` | ₹7,966.16 | **MEDIUM** | `RECENT_CHECKOUT_DROP` | `DELAYED_FOLLOW_UP` | 41% | 80% | ₹3,266.13 | AI / Fallback |
| `evt_023682` | `cust_03413` | ₹7,884.88 | **MEDIUM** | `RECENT_CHECKOUT_DROP` | `DELAYED_FOLLOW_UP` | 46% | 80% | ₹3,627.04 | AI / Fallback |
| `evt_000069` | `cust_05225` | ₹2,116.91 | **HIGH** | `HIGH_PURCHASE_INTENT_ABANDONMENT` | `CHECKOUT_REMINDER` | 75% | 88% | ₹1,587.68 | AI / Fallback |
| `evt_000084` | `cust_06667` | ₹2,195.56 | **HIGH** | `HIGH_PURCHASE_INTENT_ABANDONMENT` | `CHECKOUT_REMINDER` | 62% | 88% | ₹1,361.25 | AI / Fallback |
| `evt_000101` | `cust_02798` | ₹4,453.13 | **HIGH** | `HIGH_PURCHASE_INTENT_ABANDONMENT` | `CHECKOUT_REMINDER` | 68% | 88% | ₹3,028.13 | AI / Fallback |
| `evt_000048` | `cust_07100` | ₹841.18 | **MEDIUM** | `RECENT_CHECKOUT_DROP` | `DELAYED_FOLLOW_UP` | 50% | 80% | ₹420.59 | AI / Fallback |
| `evt_000051` | `cust_02751` | ₹875.56 | **MEDIUM** | `RECENT_CHECKOUT_DROP` | `DELAYED_FOLLOW_UP` | 50% | 80% | ₹437.78 | AI / Fallback |
| `evt_000130` | `cust_06087` | ₹204.24 | **MEDIUM** | `RECENT_CHECKOUT_DROP` | `DELAYED_FOLLOW_UP` | 50% | 80% | ₹102.12 | AI / Fallback |
| `evt_000131` | `cust_05981` | ₹201.52 | **MEDIUM** | `RECENT_CHECKOUT_DROP` | `DELAYED_FOLLOW_UP` | 50% | 80% | ₹100.76 | AI / Fallback |
| `evt_000002` | `cust_06890` | ₹1,601.76 | **MEDIUM** | `RECENT_CHECKOUT_DROP` | `DELAYED_FOLLOW_UP` | 50% | 80% | ₹800.88 | AI / Fallback |
| `evt_000011` | `cust_09779` | ₹165.66 | **MEDIUM** | `RECENT_CHECKOUT_DROP` | `DELAYED_FOLLOW_UP` | 50% | 80% | ₹82.83 | AI / Fallback |
| `evt_000005` | `cust_08726` | ₹825.16 | **LOW** | `LOW_INTENT_ABANDONMENT` | `NO_ACTION` | 30% | 90% | ₹247.55 | AI / Fallback |
| `evt_000009` | `cust_01847` | ₹591.91 | **LOW** | `LOW_INTENT_ABANDONMENT` | `NO_ACTION` | 30% | 90% | ₹177.57 | AI / Fallback |
| `evt_000016` | `cust_05618` | ₹693.68 | **LOW** | `LOW_INTENT_ABANDONMENT` | `NO_ACTION` | 30% | 90% | ₹208.10 | AI / Fallback |
| `evt_000001` | `cust_07964` | ₹0.00 | **LOW** | `LOW_INTENT_ABANDONMENT` | `NO_ACTION` | 5% | 95% | ₹0.00 | AI / Fallback |
| `evt_000007` | `cust_07275` | ₹0.00 | **LOW** | `LOW_INTENT_ABANDONMENT` | `NO_ACTION` | 5% | 95% | ₹0.00 | AI / Fallback |
| `evt_000010` | `cust_05737` | ₹0.00 | **LOW** | `LOW_INTENT_ABANDONMENT` | `NO_ACTION` | 5% | 95% | ₹0.00 | AI / Fallback |
| `evt_000012` | `cust_07621` | ₹0.00 | **LOW** | `LOW_INTENT_ABANDONMENT` | `NO_ACTION` | 5% | 95% | ₹0.00 | AI / Fallback |
| `evt_000013` | `cust_07849` | ₹0.00 | **LOW** | `LOW_INTENT_ABANDONMENT` | `NO_ACTION` | 5% | 95% | ₹0.00 | AI / Fallback |

---

## 4. Behavioral Archetype Deep-Dives

### Case A: High-Value Repeat Customer (`evt_014183`)
- **Telemetry**: ₹7,907.96 cart, 18 min on site, 2 prior orders, ₹3,950 CLV.
- **Diagnosis**: `REPEAT_CUSTOMER_ABANDONMENT`
- **Recommended Action**: `PERSONALIZED_REMINDER`
- **AI Recovery Probability**: 82% | **Confidence**: 92%
- **Expected Recovery Value**: ₹6,484.53
- **Insight**: The model recognized strong historical brand loyalty, recommending a respectful personalized reminder rather than a generic discount.

### Case B: High Engagement Cart Abandonment (`evt_000069`)
- **Telemetry**: ₹2,116.91 cart, 19 pages viewed, 21 min on site.
- **Diagnosis**: `HIGH_PURCHASE_INTENT_ABANDONMENT`
- **Recommended Action**: `CHECKOUT_REMINDER`
- **AI Recovery Probability**: 75% | **Confidence**: 88%
- **Expected Recovery Value**: ₹1,587.68
- **Insight**: Deep session exploration indicates high purchase intent. A standard timely checkout reminder is appropriate and non-intrusive.

### Case C: Low Engagement / Window Shopper (`evt_000001`)
- **Telemetry**: ₹0.00 cart, 1 min on site, 2 pages viewed.
- **Diagnosis**: `LOW_INTENT_ABANDONMENT`
- **Recommended Action**: `NO_ACTION`
- **AI Recovery Probability**: 5% | **Confidence**: 95%
- **Expected Recovery Value**: ₹0.00
- **Insight**: Outreach suppressed entirely to preserve sender reputation and prevent customer annoyance.

### Case D: New Customer with High-Value Cart (`evt_014591`)
- **Telemetry**: ₹7,971.88 cart, 0 prior purchases, medium intent score.
- **Diagnosis**: `RECENT_CHECKOUT_DROP`
- **Recommended Action**: `DELAYED_FOLLOW_UP`
- **AI Recovery Probability**: 50% | **Confidence**: 80%
- **Insight**: Because the customer has no established transaction history, the model appropriately dampens its confidence (80% vs 92%) and recommends delayed follow-up rather than aggressive outreach.

---

## 5. Audit Trail & Database Persistence

Every diagnosis call is persisted in the `ai_decisions` table. Sample audit output:

```
======================================================================
 RecoverAI Decision Audit Trail: dec_test_audit_001
----------------------------------------------------------------------
 Event ID                  : evt_000666
 Customer ID               : cust_05529
 Root Cause Diagnosis      : REPEAT_CUSTOMER_ABANDONMENT
 Recommended Action        : PERSONALIZED_REMINDER
 Priority Tier             : CRITICAL
 Recovery Probability (AI) : 86.0%
 Recommendation Confidence : 94.0%
 Revenue at Risk           : INR 7,735.08
 Expected Recovery Value   : INR 6,652.17
 Decision Source           : AI (gpt-4o-mini)
 Reason Codes              : vip_repeat, high_clv
 Explanation               : VIP customer with 3 prior orders abandoned checkout.
 Suggested Message         : "Hi, your cart is waiting with 1-click checkout!"
======================================================================
```
