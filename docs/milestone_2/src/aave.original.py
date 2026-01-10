# Simple DeFi Borrowing Simulation (Aave-style fixed LTV)
# Simulates just the borrowing mechanics against a Uniswap v3 position

#Parameters defined by Aave governance

#Loan-to-value ratio: 65%
ltv_max=0.65

#Liquidation threshold: 70%
liquidation_threshold=0.70

# A simple borrow function. Assumes maximum allowed amount is borrowed
def borrow(collateral_value_usd):

    # Calculate maximum safe borrow amount
    loan_amount = collateral_value_usd * ltv_max

    # Health factor = collateral_value / (borrowed / liquidation_threshold)
    health_factor = collateral_value_usd * liquidation_threshold / loan_amount

    return loan_amount

# A function that computes a health factor for a given position value

def calculate_health_factor(position_value, loan_amount):
    return position_value * liquidation_threshold/ loan_amount

# Run test code
position_value=10000
loan = borrow(position_value)

print("Loan amount\t" + str(loan) + " for position value\t" + str(position_value))

print ("Health factor\t" + str(calculate_health_factor(position_value, loan)))