# 📊 Executive Microfinance & Credit Risk Analytics Dashboard

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://mfi-risk-analytics.streamlit.app/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional, executive-grade portfolio quality and credit risk monitoring dashboard designed for Microfinance Institutions (MFIs) and retail lending operations. It tracks industry-standard risk metrics including **PAR30**, **PAR90 / NPL**, portfolio aging, and branch-level financial performance.

---

## 🚀 Live Demo
Experience the interactive dashboard directly in your browser:
👉 **[Launch Live Dashboard](https://mfi-risk-analytics.streamlit.app/)**

---

## 🌟 Key Features & Analytics

* **Gross Loan Portfolio (GLP) Monitoring:** Real-time visibility into total outstanding principal, active borrower counts, and average interest yields.
* **Portfolio at Risk (PAR) Tracking:** Automated calculations of crucial risk indicators:
  * **PAR30:** Portfolio at risk > 30 days (early delinquency warning).
  * **PAR90 / NPL (Non-Performing Loans):** Toxic portfolio monitoring (> 90 days overdue).
* **Portfolio Aging (Risk Buckets):** Visual distribution of outstanding balance across delinquency brackets (*Healthy, 1-30 Days, 31-90 Days, 90+ Days*).
* **Branch-Level Breakdown:** Performance comparison showing interest balances, overdue interest, and accrued penalty fees per branch location.
* **Interactive Filtering:** Sift through performance data dynamically by branch and loan status (Active vs. Closed).

---

## 💾 Core Architecture & Database

This project is built with production scalability in mind. It separates data generation, database management, and visualization into independent modules:

1. **Relational Database (`SQLite`):** A lightweight relational database containing fully structured tables:
   * `clients` (Demographics, branch assignments, unique SSNs).
   * `loans` (Outstanding balances, interest rates, maturities, daily accrued penalties, and overdue indicators).
   * `payments` (Amortization schedules tracking expected vs. actual payments, late flags, and partial repayments).
2. **Robust Synthetic Data Engine (`generate_data.py`):** Automatically generates highly realistic, randomized client portfolios, complete with historical loan disbursements, repayment cycles, and simulated delinquencies.
3. **Interactive Frontend UI (`app.py`):** A fast, responsive, and secure presentation layer powered by **Streamlit** and **Plotly** for high-end data visualization.

> 💡 **Production Ready:** Although the app currently runs on a simulated SQLite engine, the database abstraction layer is designed to easily migrate and connect to production enterprise database systems such as **Oracle SQL** or **Google BigQuery** with minimal configuration.

---

## 🛠️ Installation & Local Setup

If you want to run this project locally, follow these simple steps:

### 1. Clone the repository
```bash
git clone [https://github.com/adilgadirli/microfinance-analytics.git](https://github.com/adilgadirli/microfinance-analytics.git)
cd microfinance-analytics
