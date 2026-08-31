"""
RecoverAI Currency Utilities (Day 7)
Provides precise rupee <-> paise currency conversions for Razorpay API integration.
"""

from typing import Union


def rupees_to_paise(amount: Union[float, int, str]) -> int:
    """
    Converts INR rupee amount to integer paise for payment gateways (e.g. Razorpay).
    Examples:
      ₹100     -> 10000 paise
      ₹999.50  -> 99950 paise
      ₹14999   -> 1499900 paise
    """
    if amount is None:
        raise ValueError("Amount cannot be None for currency conversion.")
    val = float(amount)
    if val < 0:
        raise ValueError(f"Amount cannot be negative: {val}")
    return int(round(val * 100))


def paise_to_rupees(amount_paise: Union[int, float, str]) -> float:
    """
    Converts integer paise to float INR rupee amount.
    Examples:
      10000 paise   -> 100.00
      99950 paise   -> 999.50
      1499900 paise -> 14999.00
    """
    if amount_paise is None:
        raise ValueError("Amount in paise cannot be None.")
    val = float(amount_paise)
    if val < 0:
        raise ValueError(f"Amount in paise cannot be negative: {val}")
    return round(val / 100.0, 2)


__all__ = ["rupees_to_paise", "paise_to_rupees"]
