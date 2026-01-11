import pandas as pd
df = pd.read_csv('../../../data/eth-usd-max.csv', parse_dates=['date'])
df = df[['date', 'price']].sort_values('date').reset_index(drop=True)
print("Data loaded:", len(df), "days")
print(df.head())

