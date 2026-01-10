import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ------------------- 1. Load your historical data -------------------
# Adjust column names based on your CSV (e.g., from CoinGecko: 'Date', 'Close')
df = pd.read_csv('/data/eth-usd-max.csv', parse_dates=['Date'])
df = df.rename(columns={'Date': 'date', 'Close': 'price'})  # Standardize
df = df[['date', 'price']].sort_values('date').reset_index(drop=True)
print("Data loaded:", len(df), "days")
print(df.head())

# ------------------- 2. Define crashes to analyze -------------------
crashes = {
    'May 2021 Crash': ('2021-05-01', '2021-06-30'),
    'FTX Nov 2022': ('2022-11-01', '2022-11-30'),
    # Add more if you want, e.g., 'March 2020': ('2020-03-01', '2020-03-31')
}

# ------------------- 3. Impermanent Loss function -------------------
def calculate_il(price_ratio):
    """IL for full-range (infinite) position. Returns negative or zero."""
    if price_ratio <= 0:
        return -1.0  # Total loss edge case
    return 2 * np.sqrt(price_ratio) / (1 + price_ratio) - 1

def concentrated_il_scalar(range_width_pct):
    """Simple multiplier: narrower range = worse IL when price moves far.
       range_width_pct: e.g., 0.1 for ±10% range → multiplier up to ~2-3x worse."""
    # This is an approximation—narrow ranges suffer more when out-of-range
    if range_width_pct >= 2.0:  # Very wide ≈ full range
        return 1.0
    return 1 / range_width_pct  # Rough: narrower = higher penalty

# ------------------- 4. Simulate positions -------------------
num_positions = 200  # As per plan: 100-500
initial_collateral = 100000  # USD
ltv = 0.65
loan = initial_collateral * ltv

# Randomly generate position types (narrow, medium, wide ranges)
np.random.seed(42)  # Reproducible
range_widths = np.random.choice([0.2, 0.6, 1.0, 2.0], size=num_positions)
# 0.2=±10% narrow (high fee potential, high IL risk), 2.0=very wide (low IL)

results = []

for crash_name, (start, end) in crashes.items():
    period = df[(df['date'] >= start) & (df['date'] <= end)].copy()
    if len(period) == 0:
        print(f"No data for {crash_name}")
        continue

    initial_price = period['price'].iloc[0]
    period['price_ratio'] = period['price'] / initial_price

    liquidations = 0

    for i in range(num_positions):
        width = range_widths[i]
        il_scalar = concentrated_il_scalar(width)

        # Calculate IL for each day
        period['il_raw'] = calculate_il(period['price_ratio'])
        period['il_adjusted'] = period['il_raw'] * il_scalar  # Narrower = worse loss
        period['il_adjusted'] = np.minimum(period['il_adjusted'], 0)  # Cap at -100%

        # Collateral value over time
        period['collateral_value'] = initial_collateral * (1 + period['il_adjusted'])

        # Health factor
        period['health_factor'] = period['collateral_value'] / loan

        # Liquidated if health factor ever drops below 1
        if (period['health_factor'] < 1).any():
            liquidations += 1

    liquidation_rate = liquidations / num_positions
    results.append({
        'crash': crash_name,
        'positions': num_positions,
        'liquidation_rate': liquidation_rate,
        'liquidations': liquidations
    })
    print(f"{crash_name}: {liquidations}/{num_positions} liquidated ({liquidation_rate:.1%})")

# ------------------- 5. Results table -------------------
results_df = pd.DataFrame(results)
print("\nSummary:")
print(results_df)

# Optional: Quick bar chart
results_df.plot(kind='bar', x='crash', y='liquidation_rate', title='DeFi Fixed LTV Liquidation Rate (Simulated)')
plt.ylabel('Liquidation Rate')
plt.show()