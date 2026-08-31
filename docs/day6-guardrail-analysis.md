# RecoverAI — Day 6: Guardrail Engine & Risk Controls Analysis Report

> **Generated**: 2026-08-31 11:59:18 UTC  
> **Dataset**: `data/processed/recoverai_events.csv` (25,000 total events)  
> **Batch Evaluated**: 5,000 sample decisions validated through Guardrail Engine  
> **Throughput**: 1209.8 evaluations/sec (4.13 seconds total runtime)  
> **Policy Version**: `v1.1` (Merchant Defaults Enforced)

---

## 1. Executive Summary

On Day 6, RecoverAI deployed a deterministic **Guardrail Engine & Audit System** acting as the final safety, compliance, and risk checkpoint before autonomous execution. Operating strictly **after** decision selection and **before** execution (Day 7), the engine runs 10 modular, non-short-circuiting safety checks to ensure interventions are authorized, cost-effective, non-duplicative, and aligned with merchant policy.

### Key Operational & Financial Metrics
| Metric | Value | Pct (%) |
| :--- | :--- | :---: |
| **Total Evaluated Decisions** | **5,000** | 100.0% |
| **Approved (`READY_FOR_EXECUTION`)** | **627** | **12.54%** |
| **Blocked (`BLOCKED`)** | **4,373** | **87.46%** |
| **Manual Review Required (`REVIEW_REQUIRED`)** | **0** | **0.00%** |
| **Approved Expected Recoverable Revenue** | **₹1,349,437.95** | — |
| **Protected / Blocked Revenue at Risk** | **₹3,926,618.42** | — |
| **High-Value Escalated for Human Review** | **₹0.00** | — |

---

## 2. Execution State Machine Distribution

The lifecycle state machine tracks every recovery opportunity from event discovery to pre-execution readiness:

| Execution State | Count | Percentage | Description |
| :--- | :---: | :---: | :--- |
| `READY_FOR_EXECUTION` | **627** | 12.54% | Passed all 10 checks; queued for Day 7 autonomous execution. |
| `BLOCKED` | **4,373** | 87.46% | Blocked by risk threshold, zero-value cart, or merchant policy. |
| `REVIEW_REQUIRED` | **0** | 0.00% | High-value cart with uncertain signals paused for human operator sign-off. |

---

## 3. Modular Guardrail Checks Breakdown

Every candidate action is tested against 10 individual guardrails without silent short-circuiting:

| Guardrail Check | Triggered / Failed Count | Purpose & Policy Rule |
| :--- | :---: | :--- |
| `risk_threshold` | **3,721** | Blocks cases where risk score < 60.0 (low recovery potential). |
| `expected_recovery_value` | **2,599** | Enforces minimum expected recovery value (>= INR 100.00). |
| `recovery_probability` | **2,982** | Enforces minimum recovery probability (>= 40%). |
| `purchase_completion` | **2,921** | Verifies real-time status (prevents contacting completed buyers). |
| `transaction_amount_limit` | **0** | Blocks transactions exceeding maximum merchant cap (<= INR 100,000). |
| `action_permission` | **0** | Validates merchant allow_* configuration toggles. |
| `max_attempts` | **0** | Prevents spamming beyond max contact attempts (<= 2). |
| `cooldown_window` | **0** | Enforces 60-minute quiet period between outreach cycles. |
| `duplicate_action_prevention` | **0** | Idempotency guard stopping duplicate simultaneous interventions. |
| `customer_contact_frequency` | **0** | Caps customer touchpoints within 24-hour rolling window (<= 3). |
| `manual_review_filter` | **0** | Flags high-value carts (>= INR 50,000) with cold/uncertain signals. |


---

## 4. Sample Guardrail Audit Trail

Below is an excerpt of tamper-evident audit records persisted into the `guardrail_audit_logs` table:

| Event ID | Cart Value | Risk | Requested Action | Status | State | Checks Passed / Failed | Reason / Check Detail |
| :--- | :---: | :---: | :--- | :---: | :---: | :---: | :--- |
| `evt_000000` | ₹521.26 | 56.8 | `PERSONALIZED_REMINDER` | **`BLOCKED`** | `BLOCKED` | 9/10 (1 failed) | Risk score (56.8) below merchant threshold (60.0). |
| `evt_000001` | ₹0.00 | 46.0 | `NO_ACTION` | **`BLOCKED`** | `BLOCKED` | 6/10 (4 failed) | Purchase status 'browsing' is not eligible for autonomous recovery. |
| `evt_000002` | ₹1,601.76 | 49.5 | `DELAYED_FOLLOW_UP` | **`BLOCKED`** | `BLOCKED` | 9/10 (1 failed) | Risk score (49.5) below merchant threshold (60.0). |
| `evt_000003` | ₹2,410.23 | 84.0 | `NO_ACTION` | **`BLOCKED`** | `BLOCKED` | 8/10 (2 failed) | Purchase already completed. Recovery outreach blocked. |
| `evt_000004` | ₹2,642.43 | 63.0 | `CHECKOUT_REMINDER` | **`APPROVED`** | `READY_FOR_EXECUTION` | 10/10 (0 failed) | All policy and safety guardrail checks passed. |
| `evt_000005` | ₹825.16 | 38.1 | `CHECKOUT_REMINDER` | **`BLOCKED`** | `BLOCKED` | 9/10 (1 failed) | Risk score (38.1) below merchant threshold (60.0). |
| `evt_000006` | ₹2,495.32 | 87.9 | `NO_ACTION` | **`BLOCKED`** | `BLOCKED` | 8/10 (2 failed) | Purchase already completed. Recovery outreach blocked. |
| `evt_000007` | ₹0.00 | 41.5 | `NO_ACTION` | **`BLOCKED`** | `BLOCKED` | 6/10 (4 failed) | Purchase status 'browsing' is not eligible for autonomous recovery. |
| `evt_000008` | ₹1,583.76 | 55.3 | `DELAYED_FOLLOW_UP` | **`BLOCKED`** | `BLOCKED` | 9/10 (1 failed) | Risk score (55.3) below merchant threshold (60.0). |
| `evt_000009` | ₹591.91 | 32.6 | `CHECKOUT_REMINDER` | **`BLOCKED`** | `BLOCKED` | 9/10 (1 failed) | Risk score (32.6) below merchant threshold (60.0). |
| `evt_000010` | ₹0.00 | 37.8 | `NO_ACTION` | **`BLOCKED`** | `BLOCKED` | 6/10 (4 failed) | Purchase status 'browsing' is not eligible for autonomous recovery. |
| `evt_000011` | ₹165.66 | 43.6 | `PERSONALIZED_REMINDER` | **`BLOCKED`** | `BLOCKED` | 9/10 (1 failed) | Risk score (43.6) below merchant threshold (60.0). |
| `evt_000012` | ₹0.00 | 15.1 | `NO_ACTION` | **`BLOCKED`** | `BLOCKED` | 6/10 (4 failed) | Purchase status 'browsing' is not eligible for autonomous recovery. |
| `evt_000013` | ₹0.00 | 22.2 | `NO_ACTION` | **`BLOCKED`** | `BLOCKED` | 6/10 (4 failed) | Purchase status 'browsing' is not eligible for autonomous recovery. |
| `evt_000014` | ₹0.00 | 24.8 | `NO_ACTION` | **`BLOCKED`** | `BLOCKED` | 6/10 (4 failed) | Purchase status 'browsing' is not eligible for autonomous recovery. |

---

## 5. Architectural & Governance Safeguards Verified

1. **Strict Post-Decision Execution Barrier**: Guardrails execute strictly after decision selection and before execution. No live recovery calls or webhooks are dispatched prior to approval.
2. **Fail-Closed Operation**: Missing, corrupt, or unverified telemetry (payment status, customer ID, risk score) triggers immediate rejection or review, never silent approval.
3. **Idempotent Auditability**: Every evaluation produces an immutable record in `guardrail_audit_logs` with full check details, timestamp, and idempotency key.
4. **Human-in-the-Loop Escalation**: `REVIEW_REQUIRED` state safely isolates high-value or edge-case carts for human merchant supervision.
5. **API & Test Suite Verification**:
   - `POST /api/guardrails/validate` operational.
   - **65/65 passing automated tests** across all project modules.
