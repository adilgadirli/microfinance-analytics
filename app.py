import sys
import asyncio
from datetime import datetime, timedelta

# Prevent Windows asynchronous connection lost error (10054)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="Microfinance Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom CSS to inject to prevent text clipping in metrics
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        white-space: nowrap !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        white-space: nowrap !important;
    }
    </style>
""", unsafe_allow_html=True)

# Load data from microfinance.db and shift dates to current year (2026)
def load_data():
    conn = sqlite3.connect('microfinance.db')
    query_loans = """
        SELECT 
            l.id as loan_id,
            l.client_id,
            c.ssn as ssn,
            c.first_name as first_name,
            c.last_name as last_name,
            l.branch as branch,
            l.loan_amount as loan_amount,
            l.term_months as term_months,
            l.interest_rate as interest_rate,
            l.issue_date as issue_date,
            l.maturity_date as maturity_date,
            l.status,
            l.principal_balance as principal_balance,
            l.overdue_principal as overdue_principal,
            l.interest_balance as interest_balance,
            l.overdue_interest as overdue_interest,
            l.penalty as penalty,
            l.days_overdue as days_overdue
        FROM loans l
        JOIN clients c ON l.client_id = c.id
    """
    df_loans = pd.read_sql_query(query_loans, conn)
    conn.close()
    
    # Dynamically shift all dates by +365 days to align with 2026
    df_loans['issue_date'] = pd.to_datetime(df_loans['issue_date']) + pd.Timedelta(days=365)
    df_loans['maturity_date'] = pd.to_datetime(df_loans['maturity_date']) + pd.Timedelta(days=365)
    
    # Convert back to string format for display consistency
    df_loans['issue_date'] = df_loans['issue_date'].dt.strftime('%Y-%m-%d')
    df_loans['maturity_date'] = df_loans['maturity_date'].dt.strftime('%Y-%m-%d')
    
    return df_loans

try:
    df = load_data()

    # --- SIDEBAR (LEFT PANEL) ---
    st.sidebar.title("🏢 Micro Analytics")
    st.sidebar.markdown("---")
    
    branches = ['All'] + list(df['branch'].unique())
    selected_branch = st.sidebar.selectbox("📍 Branch", branches)

    statuses = ['All', 'active', 'closed']
    selected_status = st.sidebar.selectbox("📑 Loan Status", statuses)

    # Filtering logic
    filtered_df = df.copy()
    if selected_branch != 'All':
        filtered_df = filtered_df[filtered_df['branch'] == selected_branch]
    if selected_status != 'All':
        filtered_df = filtered_df[filtered_df['status'] == selected_status]

    # --- MAIN METRICS (KPIs) ---
    st.title("📊 Key Performance Indicators")
    
    total_clients_count = filtered_df['client_id'].nunique()
    total_loans_count = filtered_df.shape[0]

    active_loans = filtered_df[filtered_df['status'] == 'active']
    active_portfolio = active_loans['principal_balance'].sum()
    active_loans_count = active_loans.shape[0]
    active_clients_count = active_loans['client_id'].nunique()
    
    # PAR30 & PAR90 (NPL) formulas
    par30_volume = active_loans[active_loans['days_overdue'] >= 30]['principal_balance'].sum()
    par30_ratio = (par30_volume / active_portfolio * 100) if active_portfolio > 0 else 0.0
    
    par90_volume = active_loans[active_loans['days_overdue'] >= 90]['principal_balance'].sum()
    par90_ratio = (par90_volume / active_portfolio * 100) if active_portfolio > 0 else 0.0
    
    total_overdue_principal = active_loans['overdue_principal'].sum()
    total_penalty = active_loans['penalty'].sum()

    # Organized in 3 wide columns per row to avoid any "..." squeezing issue
    row1_col1, row1_col2, row1_col3 = st.columns(3)
    row1_col1.metric("💰 Active Portfolio", f"${active_portfolio:,.2f}")
    row1_col2.metric("💳 Active/Total Loans", f"{active_loans_count:,} / {total_loans_count:,}")
    row1_col3.metric("👤 Active/Total Clients", f"{active_clients_count:,} / {total_clients_count:,}")

    st.markdown("---")
    
    row2_col1, row2_col2, row2_col3 = st.columns(3)
    row2_col1.metric("⚠️ PAR30 Ratio", f"{par30_ratio:.2f}%")
    row2_col2.metric("🔴 PAR90 / NPL Ratio", f"{par90_ratio:.2f}%")
    row2_col3.metric("💸 Overdue Principal Outstanding", f"${total_overdue_principal:,.2f}")

    st.markdown("---")

    # --- CHARTS SECTION ---
    st.subheader("📈 Portfolio and Risk Trends (Shifted to 2026)")
    
    col_tr1, col_tr2 = st.columns(2)

    with col_tr1:
        st.markdown("**Monthly Loan Disbursement Trend**")
        trend_df = filtered_df.copy()
        trend_df['disbursement_month'] = pd.to_datetime(trend_df['issue_date']).dt.to_period('M').astype(str)
        trend_disbursed = trend_df.groupby('disbursement_month')['loan_amount'].sum().reset_index().tail(12)
        
        fig_trend1 = px.bar(
            trend_disbursed,
            x='disbursement_month',
            y='loan_amount',
            labels={'loan_amount': 'Volume ($)', 'disbursement_month': 'Month'},
            color_discrete_sequence=['#007bff']
        )
        fig_trend1.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=250)
        st.plotly_chart(fig_trend1, use_container_width=True)

    with col_tr2:
        st.markdown("**Monthly PAR30 Trend**")
        active_trend = filtered_df[filtered_df['status'] == 'active'].copy()
        active_trend['disbursement_month'] = pd.to_datetime(active_trend['issue_date']).dt.to_period('M').astype(str)
        
        trend_par = active_trend.groupby('disbursement_month').apply(
            lambda x: (x[x['days_overdue'] >= 30]['principal_balance'].sum() / x['principal_balance'].sum() * 100) if x['principal_balance'].sum() > 0 else 0,
            include_groups=False
        ).reset_index()
        trend_par.columns = ['Month', 'PAR30 %']
        trend_par = trend_par.tail(12)

        fig_trend2 = px.line(
            trend_par,
            x='Month',
            y='PAR30 %',
            markers=True,
            color_discrete_sequence=['#dc3545']
        )
        fig_trend2.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=250)
        st.plotly_chart(fig_trend2, use_container_width=True)

    # Secondary Charts Row
    st.markdown("---")
    col_dist1, col_dist2 = st.columns(2)
    
    with col_dist1:
        st.subheader("Branch Performance (Total Loan Amount)")
        branch_data = filtered_df.groupby('branch')['loan_amount'].sum().reset_index()
        fig_branch = px.bar(
            branch_data, 
            x='branch', 
            y='loan_amount', 
            text_auto='.2s',
            labels={'loan_amount': 'Total Loans ($)', 'branch': 'Branch'},
            color='branch',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_branch.update_layout(height=300)
        st.plotly_chart(fig_branch, use_container_width=True)

    with col_dist2:
        st.subheader("Loan Status Distribution")
        status_data = filtered_df['status'].value_counts().reset_index()
        status_data.columns = ['Status', 'Count']
        fig_status = px.pie(
            status_data, 
            names='Status', 
            values='Count', 
            hole=0.4,
            color_discrete_sequence=['#2ecc71', '#3498db']
        )
        fig_status.update_layout(height=300)
        st.plotly_chart(fig_status, use_container_width=True)

    st.markdown("---")

    # --- INTEREST & PENALTY STATE & RISK BUCKETS ---
    st.subheader("💵 Interest and Penalty Breakdown")
    col_tbl1, col_tbl2 = st.columns(2)

    with col_tbl1:
        st.markdown("**Interest and Penalty Balances by Branch**")
        branch_summary = filtered_df.groupby('branch').agg(
            interest_balance=('interest_balance', 'sum'),
            overdue_interest=('overdue_interest', 'sum'),
            penalty=('penalty', 'sum')
        ).reset_index()
        branch_summary.columns = ['Branch', 'Interest Balance', 'Overdue Interest', 'Accrued Penalty']
        
        st.dataframe(
            branch_summary, 
            column_config={
                "Branch": "Branch",
                "Interest Balance": st.column_config.NumberColumn("Interest Balance", format="$%,.2f"),
                "Overdue Interest": st.column_config.NumberColumn("Overdue Interest", format="$%,.2f"),
                "Accrued Penalty": st.column_config.NumberColumn("Accrued Penalty", format="$%,.2f")
            },
            use_container_width=True, 
            hide_index=True
        )

    with col_tbl2:
        st.markdown("**Loan Count and Outstanding Balance by Overdue Aging Categories**")
        
        def categorize_delay(days):
            if days == 0:
                return "0 Days (Current)"
            elif 1 <= days <= 30:
                return "1-30 Days (Early)"
            elif 31 <= days <= 90:
                return "31-90 Days (Late)"
            else:
                return "90+ Days (NPL)"
                
        active_loans_copy = active_loans.copy()
        active_loans_copy['Category'] = active_loans_copy['days_overdue'].apply(categorize_delay)
        
        cat_summary = active_loans_copy.groupby('Category').agg(
            loan_count=('loan_id', 'count'),
            balance_sum=('principal_balance', 'sum')
        ).reset_index()
        
        cat_summary.columns = ['Aging Category', 'Loan Count', 'Outstanding Balance']
        
        st.dataframe(
            cat_summary, 
            column_config={
                "Aging Category": "Aging Category",
                "Loan Count": st.column_config.NumberColumn("Loan Count", format="%d"),
                "Outstanding Balance": st.column_config.NumberColumn("Outstanding Balance", format="$%,.2f")
            },
            use_container_width=True, 
            hide_index=True
        )

    # --- WATCHLIST ---
    st.markdown("---")
    st.subheader("🔴 Delinquent Accounts Watchlist (30+ Days)")
    
    overdue_30_loans = filtered_df[
        (filtered_df['status'] == 'active') & 
        (filtered_df['days_overdue'] >= 30)
    ].sort_values(by='days_overdue', ascending=False)

    overdue_display = overdue_30_loans[[
        'ssn', 'first_name', 'last_name', 'branch', 'loan_amount', 'term_months', 
        'principal_balance', 'overdue_principal', 'interest_balance', 'overdue_interest', 'penalty', 'days_overdue'
    ]].copy()

    st.dataframe(
        overdue_display,
        column_config={
            "ssn": "SSN",
            "first_name": "First Name",
            "last_name": "Last Name",
            "branch": "Branch",
            "loan_amount": st.column_config.NumberColumn("Original Amount", format="$%,.2f"),
            "term_months": "Term (Months)",
            "principal_balance": st.column_config.NumberColumn("Remaining Principal", format="$%,.2f"),
            "overdue_principal": st.column_config.NumberColumn("Overdue Principal", format="$%,.2f"),
            "interest_balance": st.column_config.NumberColumn("Interest Balance", format="$%,.2f"),
            "overdue_interest": st.column_config.NumberColumn("Overdue Interest", format="$%,.2f"),
            "penalty": st.column_config.NumberColumn("Penalty", format="$%,.2f"),
            "days_overdue": st.column_config.NumberColumn("Days Overdue", format="%d Days 🔴")
        },
        use_container_width=True,
        hide_index=True
    )

    # --- ALL LOANS ---
    st.markdown("---")
    with st.expander("📖 General Loan Registry (All Accounts)"):
        all_display = filtered_df[[
            'ssn', 'first_name', 'last_name', 'branch', 'status', 'loan_amount', 'term_months', 
            'interest_rate', 'principal_balance', 'overdue_principal', 'interest_balance', 'days_overdue'
        ]].copy()
        
        st.dataframe(
            all_display, 
            column_config={
                "loan_amount": st.column_config.NumberColumn("Original Amount", format="$%,.2f"),
                "principal_balance": st.column_config.NumberColumn("Remaining Principal", format="$%,.2f"),
                "overdue_principal": st.column_config.NumberColumn("Overdue Principal", format="$%,.2f"),
                "interest_balance": st.column_config.NumberColumn("Interest Balance", format="$%,.2f"),
                "interest_rate": st.column_config.NumberColumn("Interest Rate", format="%.2f%%")
            },
            use_container_width=True, 
            hide_index=True
        )

except Exception as e:
    st.error(f"An error occurred: {e}")