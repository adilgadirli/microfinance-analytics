import numpy as np
import streamlit as st

# Heç bir qovluq adı olmadan, birbaşa import edirik:
from sector_config import SECTOR_CONFIGS

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Institutional Multi-Sector Credit Risk Engine",
    layout="wide"
)

st.title("📊 Credit Risk Assessment & Automated Scoring System")
st.write("Modular Core, Vertical-Specific Risk Layer Architecture compliant with international credit risk frameworks.")

# ==========================================
# 2. SIDEBAR - MODULAR SECTOR SELECTOR
# ==========================================
st.sidebar.header("💼 Credit Product Selection")
# Sektor siyahısını birbaşa config-in açarlarından (keys) çəkirik ki, adlar 100% eyni olsun
sector = st.sidebar.selectbox("Select Lending Sector", options=list(SECTOR_CONFIGS.keys()))

st.sidebar.divider()
st.sidebar.header("📥 Applicant Financials & Inputs")

inputs = {}

# Dynamic UI rendering based on selected sector
if sector == "Micro & Small Business (MSME)":
    st.sidebar.caption(SECTOR_CONFIGS[sector]["description"])
    inputs["age"] = st.sidebar.number_input("Client Age", 18, 70, 35)
    inputs["yib"] = st.sidebar.number_input("Years in Business", 0, 40, 4)
    inputs["ier"] = st.sidebar.number_input("Income-to-Expense Ratio (IER)", 0.1, 5.0, 1.8, 0.1)
    inputs["ubd"] = st.sidebar.number_input("Utility Bill Delays (Last 6 Months)", 0, 10, 1)
    inputs["loan_amount"] = st.sidebar.number_input("Requested Loan Amount ($)", 500, 50000, 5000, 500)

elif sector == "Consumer Loans":
    st.sidebar.caption(SECTOR_CONFIGS[sector]["description"])
    inputs["income"] = st.sidebar.number_input("Monthly Net Salary ($)", 200, 20000, 1200, 100)
    inputs["dti"] = st.sidebar.number_input("Debt-to-Income (DTI) Ratio %", 0, 100, 35, 5)
    inputs["bureau_delays"] = st.sidebar.number_input("Historical Bureau Delays (Days)", 0, 365, 0)
    inputs["employment_months"] = st.sidebar.number_input("Months at Current Job", 0, 240, 18)
    inputs["loan_amount"] = st.sidebar.number_input("Requested Loan Amount ($)", 300, 25000, 3000, 500)

elif sector == "Lombard (Gold/Asset Loans)":
    st.sidebar.caption(SECTOR_CONFIGS[sector]["description"])
    inputs["collateral_value"] = st.sidebar.number_input("Collateral Market Value ($)", 500, 100000, 10000, 500)
    inputs["loan_amount"] = st.sidebar.number_input("Requested Loan Amount ($)", 400, 90000, 7500, 500)
    inputs["purity_check"] = st.sidebar.checkbox("Asset Quality Verification Passed", value=True)

elif sector == "Auto Leasing":
    st.sidebar.caption(SECTOR_CONFIGS[sector]["description"])
    inputs["car_age"] = st.sidebar.number_input("Vehicle Age (Years)", 0, 25, 5)
    inputs["down_payment_pct"] = st.sidebar.number_input("Down Payment Percentage (%)", 10, 90, 30, 5)
    inputs["client_income"] = st.sidebar.number_input("Monthly Income ($)", 400, 15000, 1500, 100)
    inputs["loan_amount"] = st.sidebar.number_input("Financed Amount ($)", 2000, 100000, 15000, 1000)

# ==========================================
# 3. RISK ENGINE MATHEMATICS
# ==========================================
config = SECTOR_CONFIGS[sector]

# Calculate Probability of Default (PD) via Sigmoid Mapping
logit = config["base_logit"](inputs)
pd_value = 1 / (1 + np.exp(-logit))

# Calculate Dynamic Loss Given Default (LGD) based on sector formula
lgd_pct = config["lgd_formula"](inputs)

# Credit Score Scaling (Standard 300-850 range)
credit_score = max(300, min(850, int(850 - (pd_value * 550))))

# Expected Loss (EL) Calculation
expected_loss = pd_value * lgd_pct * inputs["loan_amount"]

# Risk-Based Pricing (APR) Recommendation
base_rate = 0.08
recommended_rate = (base_rate + (pd_value * 0.25)) * 100

# ==========================================
# 4. VISUALIZATION LAYER
# ==========================================
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("🎯 Risk Decision Matrix")
    st.metric(label="Calculated Credit Score", value=credit_score, delta=f"LGD Model: {config['lgd_type']}")
    
    if credit_score >= 680:
        st.success("🟢 STATUS: APPROVED (Low Risk)")
    elif credit_score >= 520:
        st.warning("🟡 STATUS: REFERRAL (Requires Manual Underwriting)")
    else:
        st.error("🔴 STATUS: REJECTED (High Risk)")
        
    st.divider()
    st.subheader("💸 Capital Risk Metrics")
    
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric(label="Probability of Default (PD)", value=f"{pd_value * 100:.1f}%")
    m_col2.metric(label="Loss Given Default (LGD)", value=f"{lgd_pct * 100:.1f}%")
    m_col3.metric(label="Expected Loss (EL)", value=f"${expected_loss:,.2f}")
    
    st.metric(label="Recommended Risk-Based Pricing (APR)", value=f"{recommended_rate:.2f}%")

with col2:
    st.subheader("🛠️ Architectural & Methodological Transparency")
    
    st.info(f"**Current Formula Execution:**\n- **PD Formula:** `1 / (1 + exp(-Logit))`\n- **LGD Logic:** Based on *{config['lgd_type']}* specifications.")
    
    st.markdown("### 💡 Interview Portfolio Insights")
    if sector == "Lombard (Gold/Asset Loans)":
        st.write("> **Dual-Impact Variable (LTV):** In asset-backed lending, the Loan-to-Value (LTV) ratio heavily drives both PD and LGD. A high LTV triggers stress on borrower behavior (PD) while concurrently decreasing the post-default recovery rate (LGD) due to market asset volatility.")
    elif sector == "Auto Leasing":
        st.write("> **Depreciation Curve Integration:** LGD is modeled dynamically by matching vehicle age against down-payment equity cushions, allowing automatic protection against rapid vehicle depreciation.")
    else:
        st.write("> **Regulatory Adherence:** This architecture relies on an additive scorecard matrix rather than black-box machine learning models, ensuring 100% explainability consistent with Basel III and Central Bank credit risk preferences.")


def calculate_pd(ltv, amount):
    if amount < 0:
        raise ValueError("Loan amount cannot be negative")
    
    if ltv >= 0.90:
        return 0.12 
    return 0.03