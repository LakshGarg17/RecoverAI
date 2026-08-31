"""
Day 7 Execution Analysis Batch Script
Runs demo test cases and dataset samples through the complete end-to-end recovery pipeline:
Risk Engine -> AI Diagnosis -> Decision Engine -> Guardrail Engine -> Execution Engine (Razorpay Test Mode)
Generates comprehensive analysis documentation in docs/day7-execution-analysis.md
"""

import os
import sys
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd

# Ensure root & backend paths are on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
backend_dir = os.path.join(root_dir, "backend")
for p in [root_dir, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from database.database import init_db, SessionLocal
from backend.services.execution_engine import execution_engine_service, ExecutionResult
from backend.services.decision_engine import decision_engine_service
from backend.services.guardrail_engine import guardrail_engine_service
from backend.utils.currency import paise_to_rupees


async def run_batch_execution_analysis():
    init_db()
    db = SessionLocal()

    demo_cases_path = os.path.join(root_dir, "data", "samples", "day7_demo_cases.json")
    dataset_path = os.path.join(root_dir, "data", "processed", "recoverai_events.csv")
    output_report_path = os.path.join(root_dir, "docs", "day7-execution-analysis.md")

    # 1. Run Demo Cases
    print(f"Loading Demo Test Cases from: {demo_cases_path}")
    demo_results = []
    with open(demo_cases_path, "r", encoding="utf-8") as f:
        demo_cases = json.load(f)

    for case in demo_cases:
        event_data = case["event_data"]
        case_name = case["case"]
        curr_status = case.get("current_purchase_status")

        # Run End-to-End Execution
        exec_res: ExecutionResult = await execution_engine_service.execute_decision(
            event_data=event_data,
            current_purchase_status=curr_status,
            idempotency_key=f"demo:{event_data['event_id']}:{case_name}",
            db=db,
        )

        demo_results.append({
            "case": case_name,
            "description": case.get("description", ""),
            "event_id": event_data["event_id"],
            "cart_value": event_data.get("cart_value", 0.0),
            "risk_score": event_data.get("risk_score", 0.0),
            "expected_action": case.get("expected_action"),
            "executed_action": exec_res.action,
            "status": exec_res.status,
            "execution_state": exec_res.execution_state,
            "provider": exec_res.provider,
            "payment_link_id": exec_res.payment_link_id,
            "payment_url": exec_res.payment_url,
            "reason": exec_res.reason,
        })

    # 2. Run Sample from Processed Dataset
    print(f"Loading events from: {dataset_path}")
    df = pd.read_csv(dataset_path)
    sample_size = 1000
    df_sample = df.head(sample_size)

    start_time = time.time()
    batch_stats = {
        "total_evaluated": 0,
        "created_payment_links": 0,
        "created_internal_reminders": 0,
        "rejected_guardrails": 0,
        "failed_executions": 0,
        "total_attempted_value": 0.0,
        "total_protected_value": 0.0,
        "actions_breakdown": {},
    }

    sample_audit_trail = []

    for idx, row in df_sample.iterrows():
        ev_data = row.to_dict()
        evt_id = str(ev_data.get("event_id"))
        cart_val = float(ev_data.get("cart_value") or 0.0)

        # Execute decision
        res = await execution_engine_service.execute_decision(
            event_data=ev_data,
            idempotency_key=f"batch7:{evt_id}",
            db=db,
        )

        batch_stats["total_evaluated"] += 1
        action_name = res.action
        batch_stats["actions_breakdown"][action_name] = batch_stats["actions_breakdown"].get(action_name, 0) + 1

        if res.status == "CREATED":
            if res.payment_link_id:
                batch_stats["created_payment_links"] += 1
            else:
                batch_stats["created_internal_reminders"] += 1
            batch_stats["total_attempted_value"] += cart_val
        elif res.status == "REJECTED":
            batch_stats["rejected_guardrails"] += 1
            batch_stats["total_protected_value"] += cart_val
        else:
            batch_stats["failed_executions"] += 1

        if idx < 12:
            sample_audit_trail.append({
                "event_id": evt_id,
                "cart_value": cart_val,
                "risk_score": float(ev_data.get("risk_score") or 0.0),
                "action": res.action,
                "status": res.status,
                "provider": res.provider,
                "payment_link_id": res.payment_link_id or "—",
                "reason": res.reason or "Approved & Dispatched",
            })

    elapsed = time.time() - start_time
    throughput = batch_stats["total_evaluated"] / elapsed if elapsed > 0 else 0
    db.close()

    print(f"Evaluated {batch_stats['total_evaluated']} events in {elapsed:.2f}s ({throughput:.1f} events/sec).")

    # 3. Generate Markdown Report
    os.makedirs(os.path.dirname(output_report_path), exist_ok=True)
    with open(output_report_path, "w", encoding="utf-8") as f:
        f.write("# RecoverAI — Day 7: Razorpay Test Mode & Recovery Execution Analysis Report\n\n")
        f.write(f"> **Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}  \n")
        f.write(f"> **Integration**: Razorpay Test Mode (`rzp_test_...`) + Currency Conversion (Paise Precision)  \n")
        f.write(f"> **Batch Evaluated**: {batch_stats['total_evaluated']:,} events evaluated through complete pipeline  \n")
        f.write(f"> **Throughput**: {throughput:.1f} evaluations/sec ({elapsed:.2f} seconds total runtime)  \n\n")
        f.write("---\n\n")

        f.write("## 1. Executive Summary\n\n")
        f.write("On Day 7, RecoverAI connected its deterministic **Guardrail & Decision Layer** to a live **Recovery Execution Layer** operating in **Razorpay Test Mode**.\n\n")
        f.write("### Strict Security & Architectural Invariants Enforced:\n")
        f.write("1. **Test Mode Exclusivity**: All external payment links are generated in Razorpay Test Mode (`https://rzp.io/...`). No real funds move.\n")
        f.write("2. **AI Indirectness Barrier**: The AI model *never* calls Razorpay directly. Flow is strictly: `Event` -> `Risk Engine` -> `AI Diagnosis` -> `Decision Engine` -> `Guardrail Engine` -> `Execution Engine` -> `Razorpay`.\n")
        f.write("3. **Independent Pre-Execution Verification**: The execution layer re-verifies guardrails live immediately before triggering Razorpay, preventing stale execution.\n")
        f.write("4. **Zero-Duplicate Idempotency**: Repeated calls return the existing active execution rather than generating duplicate Razorpay payment links.\n\n")

        f.write("### Execution Performance & Financial Summary\n\n")
        f.write("| Metric | Value | Percentage |\n")
        f.write("| :--- | :--- | :---: |\n")
        f.write(f"| **Total Processed Decisions** | **{batch_stats['total_evaluated']:,}** | 100.0% |\n")
        f.write(f"| **Dispatched Razorpay Payment Links** | **{batch_stats['created_payment_links']:,}** | {batch_stats['created_payment_links']/batch_stats['total_evaluated']*100:.2f}% |\n")
        f.write(f"| **Internal Reminders Dispatched** | **{batch_stats['created_internal_reminders']:,}** | {batch_stats['created_internal_reminders']/batch_stats['total_evaluated']*100:.2f}% |\n")
        f.write(f"| **Blocked by Pre-Execution Guardrails** | **{batch_stats['rejected_guardrails']:,}** | {batch_stats['rejected_guardrails']/batch_stats['total_evaluated']*100:.2f}% |\n")
        f.write(f"| **Total Recoverable Value Dispatched** | **₹{batch_stats['total_attempted_value']:,.2f}** | — |\n")
        f.write(f"| **Protected Value (Zero Outreach Spam)** | **₹{batch_stats['total_protected_value']:,.2f}** | — |\n\n")

        f.write("---\n\n")
        f.write("## 2. Demo Test Cases Validation\n\n")
        f.write("Illustrative end-to-end scenarios run through the pipeline:\n\n")
        f.write("| Demo Case | Cart Value | Risk Score | Action | Status | Provider | Payment Link / Outcome |\n")
        f.write("| :--- | :---: | :---: | :--- | :---: | :---: | :--- |\n")
        for dc in demo_results:
            plink_disp = f"[`{dc['payment_link_id']}`]({dc['payment_url']})" if dc['payment_link_id'] else "—"
            f.write(f"| `{dc['case']}` | ₹{dc['cart_value']:,.2f} | {dc['risk_score']:.1f} | `{dc['executed_action']}` | **`{dc['status']}`** | `{dc['provider']}` | {plink_disp} |\n")

        f.write("\n---\n\n")
        f.write("## 3. Sample Execution & Audit Trail\n\n")
        f.write("| Event ID | Cart Value | Risk | Selected Action | Status | Provider | Payment Link ID | Execution Reason / Audit |\n")
        f.write("| :--- | :---: | :---: | :--- | :---: | :---: | :---: | :--- |\n")
        for st in sample_audit_trail:
            f.write(f"| `{st['event_id']}` | ₹{st['cart_value']:,.2f} | {st['risk_score']:.1f} | `{st['action']}` | **`{st['status']}`** | `{st['provider']}` | `{st['payment_link_id']}` | {st['reason'][:55]} |\n")

        f.write("\n---\n\n")
        f.write("## 4. Recovery Lifecycle State Machine\n\n")
        f.write("RecoverAI faithfully tracks the complete financial recovery progression:\n\n")
        f.write("```mermaid\n")
        f.write("stateDiagram-v2\n")
        f.write("    [*] --> REVENUE_AT_RISK: Event Discovered\n")
        f.write("    REVENUE_AT_RISK --> RECOVERY_IDENTIFIED: Risk Engine Scored\n")
        f.write("    RECOVERY_IDENTIFIED --> AI_DIAGNOSED: AI Diagnosis Agent\n")
        f.write("    AI_DIAGNOSED --> ACTION_RECOMMENDED: Decision Engine Selected\n")
        f.write("    ACTION_RECOMMENDED --> GUARDRAIL_PENDING: Safety Check\n")
        f.write("    GUARDRAIL_PENDING --> BLOCKED: Policy / Risk Violations\n")
        f.write("    GUARDRAIL_PENDING --> REVIEW_REQUIRED: High-Value Review\n")
        f.write("    GUARDRAIL_PENDING --> APPROVED: All 10 Checks Passed\n")
        f.write("    APPROVED --> READY_FOR_EXECUTION: Pre-Execution Re-verification\n")
        f.write("    READY_FOR_EXECUTION --> PAYMENT_LINK_CREATED: Razorpay Test Mode\n")
        f.write("    PAYMENT_LINK_CREATED --> PAYMENT_PENDING: Customer Outreach\n")
        f.write("    PAYMENT_PENDING --> PAYMENT_SUCCESS: Webhook Verified\n")
        f.write("    PAYMENT_SUCCESS --> REVENUE_RECOVERED: Ledger Updated\n")
        f.write("    PAYMENT_PENDING --> PAYMENT_FAILED: Webhook Declined\n")
        f.write("    PAYMENT_PENDING --> PAYMENT_EXPIRED: 60m Cooldown\n")
        f.write("```\n\n")

        f.write("---\n\n")
        f.write("## 5. Webhook Reconciliations & Audit Verification\n\n")
        f.write("1. **Cryptographic Integrity**: `POST /api/webhooks/razorpay` verifies `X-Razorpay-Signature` using HMAC SHA256 before parsing entity state.\n")
        f.write("2. **Payment Success**: `payment_link.paid` / `payment.captured` transitions `RecoveryExecution` to `SUCCEEDED` and creates an immutable `RecoveryRecord` with `recovered_amount` and `payment_id`.\n")
        f.write("3. **Payment Failure**: `payment.failed` captures `error_code` and `error_description` without auto-retry, respecting safety cooldowns.\n")
        f.write("4. **Payment Expiration**: `payment_link.expired` transitions state to `EXPIRED` cleanly.\n")
        f.write("5. **Audit Trail**: Every execution and webhook trigger is logged into `guardrail_audit_logs`.\n")

    print(f"Report successfully written to: {output_report_path}")


if __name__ == "__main__":
    asyncio.run(run_batch_execution_analysis())
