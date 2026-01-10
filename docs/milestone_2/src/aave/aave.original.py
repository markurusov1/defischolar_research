# Simple DeFi Borrowing Simulation (Aave-style fixed LTV)
# Simulates just the borrowing mechanics against a Uniswap v3 position

# Parameters defined by Aave governance

ltv_max = 0.65  # Loan to value ratio
liquidation_threshold = 0.70
close_factor = 0.5
liquidation_bonus = 0.10


# A function that computes a health factor for a given position value
def calculate_health_factor(position_value, loan_amount):
    """
    Compute health factor HF = (position_value * liquidation_threshold) / loan_amount.
    If loan_amount is zero or negative, return +inf to indicate no outstanding debt (or invalid loan).
    """
    if loan_amount <= 0:
        return float("inf")
    return position_value * liquidation_threshold / loan_amount


# A simple borrow function. Assumes maximum allowed amount is borrowed
def borrow(collateral_value_usd):
    # Calculate maximum safe borrow amount
    loan_amount = collateral_value_usd * ltv_max

    # Note: don't compute health factor here in a way that can divide by zero; callers can use
    # calculate_health_factor(…) which already guards loan_amount <= 0.
    return loan_amount


# Decide whether a position should be liquidated and how much to liquidate
def decide_liquidation(position_value, loan_amount):

    # Guard against zero or negative loan amounts
    if loan_amount <= 0:
        return {
            "should_liquidate": False,
            "health_factor": float("inf"),
            "repay_amount": 0.0,
            "collateral_to_take": 0.0,
        }

    hf = calculate_health_factor(position_value, loan_amount)

    if hf < 1.0:
        repay = loan_amount * close_factor
        collateral_taken = repay * (1 + liquidation_bonus)
        return {
            "should_liquidate": True,
            "health_factor": hf,
            "repay_amount": repay,
            "collateral_to_take": collateral_taken,
        }

    return {
        "should_liquidate": False,
        "health_factor": hf,
        "repay_amount": 0.0,
        "collateral_to_take": 0.0,
    }


# Example usage when run as a script; keep module import-friendly
if __name__ == "__main__":
    # Run test code
    position_value = 10000
    loan = borrow(position_value)

    print("Loan amount\t" + str(loan) + " for position value\t" + str(position_value))

    print("Health factor\t" + str(calculate_health_factor(position_value, loan)))

    # Show a liquidation decision example
    decision = decide_liquidation(position_value, loan)
    print("Liquidation decision:\t" + str(decision))
