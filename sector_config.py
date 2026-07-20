# sector_config.py
import numpy as np

SECTOR_CONFIGS = {
    "Micro & Small Business (MSME)": {
        "description": "Focus: Cash Flow Sustainability & Alternative Willingness to Pay.",
        "lgd_type": "Fixed Industry Average (Unsecured)",
        "lgd_formula": lambda inputs: 0.45,
        "base_logit": lambda inputs: 3.5 - (inputs["yib"] * 0.3) - (inputs["ier"] * 0.8) + (inputs["ubd"] * 0.6) + (25 - inputs["age"] if inputs["age"] < 25 else 0) * 0.1
    },
    "Consumer Loans": {
        "description": "Focus: Formal Employment, Credit Bureau History & Debt Load.",
        "lgd_type": "Fixed Retail Average (High Risk)",
        "lgd_formula": lambda inputs: 0.60,
        # Balanslaşdırılmış və kalibrasiya olunmuş risk formulası
        "base_logit": lambda inputs: 0.5 + (inputs["dti"] * 0.02) + (inputs["bureau_delays"] * 0.04) - (inputs["employment_months"] * 0.01) - (inputs["income"] * 0.0004)
    },
    "Lombard (Gold/Asset Loans)": {
        "description": "Focus: Asset Valuation & Loan-to-Value (LTV) Safety Margins.",
        "lgd_type": "Dynamic LTV-Based Recovery",
        "lgd_formula": lambda inputs: max(0.05, 1 - (1 / (inputs["loan_amount"] / inputs["collateral_value"]))), 
        "base_logit": lambda inputs: -2.5 + (((inputs["loan_amount"] / inputs["collateral_value"]) * 100) * 0.06) + (0 if inputs["purity_check"] else 4.0)
    },
    "Auto Leasing": {
        "description": "Focus: Asset Depreciation, Down Payment & Client Capacity.",
        "lgd_type": "Depreciation & Liquidity Matrix",
        "lgd_formula": lambda inputs: min(0.50, 0.15 + (inputs["car_age"] * 0.015) - (inputs["down_payment_pct"] * 0.002)),
        "base_logit": lambda inputs: 1.0 + (inputs["car_age"] * 0.2) - (inputs["down_payment_pct"] * 0.04) - (inputs["client_income"] * 0.0003)
    }
}