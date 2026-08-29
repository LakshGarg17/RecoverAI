"""
Script to evaluate 25 diverse real dataset events for docs/day4-ai-evaluation.md
"""

import asyncio
import os
import sys
import pandas as pd

# Add root & backend paths
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from ai.diagnosis import ai_diagnosis_agent, get_processed_dataset


async def generate_evaluation_table():
    df = get_processed_dataset()

    # 1. High-value abandoned carts
    top_abandoned = df[df["event_type"] == "cart_abandoned"].sort_values("amount", ascending=False).head(8)
    # 2. Loyal repeat buyers with carts
    repeat_abandoned = df[(df["event_type"] == "cart_abandoned") & (df["purchase_history"] >= 2)].head(7)
    # 3. First-time buyers with carts
    new_abandoned = df[(df["event_type"] == "cart_abandoned") & (df["purchase_history"] == 0)].head(5)
    # 4. Browsing sessions (zero cart)
    low_events = df[df["event_type"] == "page_browse"].head(5)

    sample_df = pd.concat([top_abandoned, repeat_abandoned, new_abandoned, low_events], ignore_index=True)

    print("| Event ID | Customer ID | Cart Value | Priority | Diagnosis | AI Action | Recovery Prob. | Confidence | Expected Recovery |")
    print("| :--- | :--- | :---: | :---: | :--- | :--- | :---: | :---: | :---: |")

    for _, row in sample_df.iterrows():
        res = await ai_diagnosis_agent.diagnose_event(row)
        d = res.model_dump()
        print(
            f"| `{d['event_id']}` | `{d['customer_id']}` | INR {d['revenue_at_risk']:,.2f} | "
            f"**{d['priority']}** | `{d['diagnosis']}` | `{d['recommended_action']}` | "
            f"{d['recovery_probability']*100:.0f}% | {d['recommendation_confidence']*100:.0f}% | "
            f"INR {d['expected_recovery_value']:,.2f} |"
        )


if __name__ == "__main__":
    asyncio.run(generate_evaluation_table())
