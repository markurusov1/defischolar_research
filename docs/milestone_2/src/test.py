import pandas as pd
df = pd.read_csv('../../../data/eth-usd-max.csv', parse_dates=['date'])
df = df[['date', 'price']].sort_values('date').reset_index(drop=True)
print("Data loaded:", len(df), "days")
print(df.head())

# ------------------- 2. Define crashes to analyze -------------------
crashes = {
    'May 2021 Crash': ('2021-05-01', '2021-06-30'),
    'FTX Nov 2022': ('2022-11-01', '2022-11-30'),
}