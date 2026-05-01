"""Tests for option yield calculator."""
import json
import os
import sys
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from option_yield_calculator import calculate_annualized_return, validate_input, main


def test_basic_put_calculation():
    """Test basic sell put calculation (Duan Yongping AAPL example)."""
    result = calculate_annualized_return(
        strike=195.00,
        premium=14.45,
        months=7,
        risk_free_rate=0.043,
        quantity=999,
        shares_per_contract=100,
    )
    assert abs(result['capital_per_share'] - 180.55) < 0.01
    assert abs(result['premium_annualized_return'] - 0.137) < 0.01
    assert abs(result['total_annualized_return'] - 0.180) < 0.01
    assert result['shares_total'] == 99900
    assert abs(result['total_premium_income'] - 1443555.00) < 1.0


def test_basic_call_calculation():
    """Test basic sell call calculation."""
    result = calculate_annualized_return(
        strike=200.00,
        premium=5.00,
        months=3,
        risk_free_rate=0.04,
        quantity=10,
        shares_per_contract=100,
    )
    assert abs(result['capital_per_share'] - 195.00) < 0.01
    # (5 / 195) * (12/3) = 0.1026
    assert abs(result['premium_annualized_return'] - 0.1026) < 0.01
    # 0.1026 + 0.04 = 0.1426
    assert abs(result['total_annualized_return'] - 0.1426) < 0.01
    assert result['shares_total'] == 1000


def test_hk_market_with_custom_shares():
    """Test HK market with non-standard shares per contract."""
    result = calculate_annualized_return(
        strike=300.00,
        premium=10.00,
        months=6,
        risk_free_rate=0.035,
        quantity=5,
        shares_per_contract=500,
    )
    assert result['shares_total'] == 2500
    assert abs(result['capital_per_share'] - 290.00) < 0.01
    # (10 / 290) * (12/6) = 0.0690
    assert abs(result['premium_annualized_return'] - 0.0690) < 0.01


def test_small_premium():
    """Test with very small premium."""
    result = calculate_annualized_return(
        strike=100.00,
        premium=0.50,
        months=1,
        risk_free_rate=0.04,
        quantity=1,
        shares_per_contract=100,
    )
    assert abs(result['capital_per_share'] - 99.50) < 0.01
    # (0.5 / 99.5) * 12 = 0.0603
    assert abs(result['premium_annualized_return'] - 0.0603) < 0.01


def test_validate_input_valid():
    """Test input validation with valid data."""
    errors = validate_input(
        strike=195.00,
        premium=14.45,
        months=7,
        risk_free_rate=0.043,
    )
    assert errors == []


def test_validate_input_premium_exceeds_strike():
    """Test that premium >= strike is rejected."""
    errors = validate_input(
        strike=100.00,
        premium=150.00,
        months=7,
        risk_free_rate=0.043,
    )
    assert len(errors) > 0
    assert any('权利金' in e for e in errors)


def test_validate_input_expired():
    """Test that expired options are rejected."""
    errors = validate_input(
        strike=100.00,
        premium=5.00,
        months=0,
        risk_free_rate=0.043,
    )
    assert len(errors) > 0
    assert any('过期' in e for e in errors)


def test_validate_input_negative_months():
    """Test that negative months are rejected."""
    errors = validate_input(
        strike=100.00,
        premium=5.00,
        months=-1,
        risk_free_rate=0.043,
    )
    assert len(errors) > 0


def test_main_with_json_files():
    """Test main() reads input JSON and writes output JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'input.json')
        output_path = os.path.join(tmpdir, 'output.json')

        input_data = {
            "underlying": "AAPL",
            "market": "us",
            "option_type": "put",
            "strike": 195.00,
            "premium": 14.45,
            "months": 7,
            "quantity": 999,
            "shares_per_contract": 100,
            "risk_free_rate": 0.043,
        }
        with open(input_path, 'w') as f:
            json.dump(input_data, f)

        # Patch sys.argv
        old_argv = sys.argv
        sys.argv = ['option_yield_calculator.py', input_path, output_path]
        try:
            main()
        finally:
            sys.argv = old_argv

        with open(output_path, 'r') as f:
            result = json.load(f)

        assert result['underlying'] == 'AAPL'
        assert result['market'] == 'us'
        assert abs(result['capital_per_share'] - 180.55) < 0.01
        assert abs(result['total_annualized_return'] - 0.180) < 0.01
