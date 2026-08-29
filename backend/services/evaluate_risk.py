"""
Proxy script to run portfolio risk evaluation from backend/services/evaluate_risk.py
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
pipeline_dir = os.path.abspath(os.path.join(current_dir, "..", "data_pipeline"))
if pipeline_dir not in sys.path:
    sys.path.insert(0, pipeline_dir)

from evaluate_risk import run_portfolio_risk_evaluation

if __name__ == "__main__":
    run_portfolio_risk_evaluation()
