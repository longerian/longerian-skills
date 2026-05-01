#!/usr/bin/env python3
"""Option Premium Annualized Return Calculator.

Calculates the annualized return on selling options (puts/calls)
based on Duan Yongping's method:
- Capital = Strike - Premium (net investment)
- Premium return = (Premium / Capital) × (12 / Months)
- Total return = Premium return + Risk-free rate

No external dependencies - uses only Python standard library.

Usage:
    python3 option_yield_calculator.py [input_json_path] [output_json_path]

Defaults:
    input:  ~/.longerian/data/option-yield/option_input.json
    output: ~/.longerian/data/option-yield/option_result.json
"""

import json
import os
import sys


def validate_input(strike, premium, months, risk_free_rate):
    """Validate input parameters. Returns list of error messages."""
    errors = []
    if premium >= strike:
        errors.append(f"权利金 ({premium}) 必须小于行权价 ({strike})")
    if months <= 0:
        errors.append(f"到期月数 ({months}) 必须大于 0（期权已过期）")
    if risk_free_rate < 0:
        errors.append(f"无风险利率 ({risk_free_rate}) 不能为负数")
    return errors


def calculate_annualized_return(strike, premium, months, risk_free_rate,
                                 quantity=1, shares_per_contract=100):
    """Calculate annualized return for a sold option.

    Args:
        strike: Strike price
        premium: Premium received per share
        months: Months to expiration
        risk_free_rate: Annual risk-free rate (e.g., 0.043 for 4.3%)
        quantity: Number of contracts
        shares_per_contract: Shares per contract (US: 100, HK: varies)

    Returns:
        dict with calculation results
    """
    capital_per_share = strike - premium
    shares_total = quantity * shares_per_contract
    total_premium_income = premium * shares_total

    premium_annualized_return = (premium / capital_per_share) * (12 / months)
    total_annualized_return = premium_annualized_return + risk_free_rate

    return {
        "capital_per_share": round(capital_per_share, 2),
        "shares_total": shares_total,
        "total_premium_income": round(total_premium_income, 2),
        "premium_annualized_return": round(premium_annualized_return, 4),
        "total_annualized_return": round(total_annualized_return, 4),
    }


def main():
    """CLI entry point."""
    base_dir = os.path.expanduser('~/.longerian/data/option-yield')
    input_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(base_dir, 'option_input.json')
    output_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(base_dir, 'option_result.json')

    # Load input
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    strike = data['strike']
    premium = data['premium']
    months = data['months']
    risk_free_rate = data['risk_free_rate']
    quantity = data.get('quantity', 1)
    shares_per_contract = data.get('shares_per_contract', 100)

    # Validate
    errors = validate_input(strike, premium, months, risk_free_rate)
    if errors:
        print("Error: " + "; ".join(errors), file=sys.stderr)
        sys.exit(1)

    # Calculate
    result = calculate_annualized_return(
        strike=strike,
        premium=premium,
        months=months,
        risk_free_rate=risk_free_rate,
        quantity=quantity,
        shares_per_contract=shares_per_contract,
    )

    # Merge input fields into output
    output = {
        "underlying": data.get("underlying", ""),
        "market": data.get("market", ""),
        "option_type": data.get("option_type", ""),
        "strike": strike,
        "premium": premium,
        "months": months,
        "quantity": quantity,
        "shares_per_contract": shares_per_contract,
        "risk_free_rate": risk_free_rate,
        "risk_free_rate_source": data.get("risk_free_rate_source", ""),
        "risk_free_rate_date": data.get("risk_free_rate_date", ""),
        **result,
    }

    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
