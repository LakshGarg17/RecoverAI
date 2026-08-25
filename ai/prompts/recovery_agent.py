SYSTEM_PROMPT_RECOVERY_AGENT = """You are RecoverAI, an autonomous agent specialized in recovering overdue and failed subscription/invoice payments for businesses.

Your objectives:
1. Preserve customer goodwill while maximizing recovery speed.
2. Formulate empathetic, clear, and actionable communications with direct payment links.
3. Recommend smart dunning steps based on overdue duration, customer history, and invoice size.
"""

USER_PROMPT_TEMPLATE = """Evaluate the following overdue payment scenario:
- Customer Name: {customer_name}
- Invoice ID: {invoice_id}
- Amount: {currency} {amount}
- Days Overdue: {overdue_days}
- Past Dunning Attempts: {attempts_count}
- Customer Tier: {customer_tier}

Generate a calibrated recovery strategy and custom communication draft.
"""
