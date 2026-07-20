import pytest
from credit_scoring import calculate_pd

def test_ltv_high_risk():
    assert calculate_pd(ltv=0.90, amount=1000) > 0.10 

def test_negative_loan_amount():
    with pytest.raises(ValueError):
        calculate_pd(ltv=0.50, amount=-100)