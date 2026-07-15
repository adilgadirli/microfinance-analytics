import sqlite3
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker('en_US')
random.seed(42)

BRANCHES = ['Branch 1', 'Branch 2', 'Branch 3', 'Branch 4']
PENALTY_RATE = 0.001  # 0.1% daily
TODAY = datetime(2025, 1, 1)

conn = sqlite3.connect('microfinance.db')
cursor = conn.cursor()

cursor.executescript('''
    DROP TABLE IF EXISTS payments;
    DROP TABLE IF EXISTS loans;
    DROP TABLE IF EXISTS clients;

    CREATE TABLE clients (
        id INTEGER PRIMARY KEY,
        ssn TEXT UNIQUE,
        first_name TEXT,
        last_name TEXT,
        date_of_birth TEXT,
        phone TEXT,
        branch TEXT
    );

    CREATE TABLE loans (
        id INTEGER PRIMARY KEY,
        client_id INTEGER,
        branch TEXT,
        loan_amount REAL,
        term_months INTEGER,
        interest_rate REAL,
        issue_date TEXT,
        maturity_date TEXT,
        status TEXT,
        principal_balance REAL,
        overdue_principal REAL,
        interest_balance REAL,
        overdue_interest REAL,
        penalty REAL,
        days_overdue INTEGER,
        FOREIGN KEY (client_id) REFERENCES clients(id)
    );

    CREATE TABLE payments (
        id INTEGER PRIMARY KEY,
        loan_id INTEGER,
        month_number INTEGER,
        scheduled_date TEXT,
        actual_date TEXT,
        principal_amount REAL,
        interest_amount REAL,
        status TEXT,
        FOREIGN KEY (loan_id) REFERENCES loans(id)
    );
''')

# ── 1. CLIENTS ───────────────────────────────────────────────────────
print("Generating clients...")
ssn_set = set()

def unique_ssn():
    while True:
        ssn = ''.join([str(random.randint(0, 9)) for _ in range(12)])
        if ssn not in ssn_set:
            ssn_set.add(ssn)
            return ssn

clients = []
for i in range(1, 1128):
    branch = random.choice(BRANCHES)
    clients.append((
        i,
        unique_ssn(),
        fake.first_name(),
        fake.last_name(),
        fake.date_of_birth(minimum_age=18, maximum_age=65).strftime('%Y-%m-%d'),
        fake.phone_number(),
        branch
    ))

cursor.executemany('''
    INSERT INTO clients (id, ssn, first_name, last_name, date_of_birth, phone, branch)
    VALUES (?, ?, ?, ?, ?, ?, ?)
''', clients)

# ── 2. LOANS & PAYMENTS ──────────────────────────────────────────────
print("Generating loans and payments...")

loan_id = 1
payment_id = 1
loans = []
payments = []

for client_id, _, _, _, _, _, branch in clients:
    num_loans = random.randint(1, 2)

    for _ in range(num_loans):
        amount = round(random.uniform(500, 15000), 2)
        term = random.choice([3, 6, 12, 18, 24])
        rate = round(random.uniform(18, 36), 2)
        monthly_rate = rate / 12 / 100

        issue_date = TODAY - timedelta(days=random.randint(30, 900))
        maturity_date = issue_date + timedelta(days=term * 30)
        status = 'active' if maturity_date > TODAY else 'closed'

        monthly_principal = round(amount / term, 2)
        monthly_interest = round(amount * monthly_rate, 2)

        months_elapsed = min(int((TODAY - issue_date).days / 30), term)

        payment_statuses = []
        for m in range(1, months_elapsed + 1):
            if random.random() < 0.25:
                delay = random.randint(5, 90)
                payment_statuses.append(('overdue', delay))
            else:
                payment_statuses.append(('paid', 0))

        overdue_principal = 0.0
        overdue_interest = 0.0
        max_days_overdue = 0

        for idx, (st, delay) in enumerate(payment_statuses):
            scheduled = issue_date + timedelta(days=30 * (idx + 1))
            actual_date = None
            pay_status = 'paid'

            if st == 'overdue':
                actual = scheduled + timedelta(days=delay)
                if actual > TODAY:
                    actual_date = None
                    overdue_principal += monthly_principal
                    overdue_interest += monthly_interest
                    days_late = (TODAY - scheduled).days
                    max_days_overdue = max(max_days_overdue, days_late)
                    pay_status = 'overdue'
                else:
                    actual_date = actual.strftime('%Y-%m-%d')
                    pay_status = 'paid_late'
            else:
                actual_date = (scheduled + timedelta(days=random.randint(-1, 2))).strftime('%Y-%m-%d')

            payments.append((
                payment_id,
                loan_id,
                idx + 1,
                scheduled.strftime('%Y-%m-%d'),
                actual_date,
                monthly_principal,
                monthly_interest,
                pay_status
            ))
            payment_id += 1

        for idx in range(months_elapsed, term):
            scheduled = issue_date + timedelta(days=30 * (idx + 1))
            payments.append((
                payment_id,
                loan_id,
                idx + 1,
                scheduled.strftime('%Y-%m-%d'),
                None,
                monthly_principal,
                monthly_interest,
                'pending'
            ))
            payment_id += 1

        principal_balance = round(monthly_principal * (term - months_elapsed), 2)
        interest_balance = round(monthly_interest * (term - months_elapsed), 2)
        penalty = round(overdue_principal * PENALTY_RATE * max_days_overdue, 2)

        loans.append((
            loan_id,
            client_id,
            branch,
            amount,
            term,
            rate,
            issue_date.strftime('%Y-%m-%d'),
            maturity_date.strftime('%Y-%m-%d'),
            status,
            principal_balance,
            round(overdue_principal, 2),
            interest_balance,
            round(overdue_interest, 2),
            penalty,
            max_days_overdue
        ))
        loan_id += 1

cursor.executemany('''
    INSERT INTO loans (
        id, client_id, branch, loan_amount, term_months, interest_rate,
        issue_date, maturity_date, status,
        principal_balance, overdue_principal,
        interest_balance, overdue_interest,
        penalty, days_overdue
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', loans)

cursor.executemany('''
    INSERT INTO payments (
        id, loan_id, month_number, scheduled_date, actual_date,
        principal_amount, interest_amount, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
''', payments)

conn.commit()

# ── 3. SUMMARY ───────────────────────────────────────────────────────
print("\n── Summary ──")
cursor.execute("SELECT COUNT(*) FROM clients")
print(f"Clients: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM loans")
print(f"Loans: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM payments")
print(f"Payments: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM loans WHERE overdue_principal > 0")
print(f"Overdue loans: {cursor.fetchone()[0]}")

cursor.execute("""
    SELECT
        SUM(CASE WHEN days_overdue >= 30 THEN overdue_principal ELSE 0 END) * 100.0
        / SUM(loan_amount) as par30
    FROM loans WHERE status = 'active'
""")
par30 = cursor.fetchone()[0]
print(f"PAR30: {par30:.2f}%")

cursor.execute("SELECT branch, COUNT(*) FROM loans GROUP BY branch")
print("\nLoans by branch:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
print("\n✅ Database created: microfinance.db")
