# hybrid_stress_sim.py
# Implements TradFi-style dynamic margin via stress-adjusted loan amount
# Reduces borrow on risky positions instead of raising liquidation threshold
# Added timestamp to output directory

import os
import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime

# ────────────────────────────────────────────────
# Import your existing modules
# ────────────────────────────────────────────────
from position_loader import create_positions, N_POSITIONS
from uniswap.il_v3 import UniswapV3Position
from aave.aave_original import AaveSimulator

# ────────────────────────────────────────────────
# Step 1: Upfront Preparation (run once)
# ────────────────────────────────────────────────

def load_historical_data() -> pd.DataFrame:
    """Load ETH price data (assumes data_loader.py exposes df)"""
    try:
        import data_loader
        df = data_loader.df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        return df[['date', 'open_price', 'close_price']]
    except Exception as e:
        raise RuntimeError("Could not load price data from data_loader") from e


def prepare_positions_pool(n_positions: int = N_POSITIONS) -> List[UniswapV3Position]:
    """Create the fixed pool of positions (same across all dates)"""
    return create_positions(n_positions=n_positions)


# TradFi stress test parameters
SHOCK_LEVELS_PCT = np.array([-15,-12, -9,-6,-3, 0, 3, 6, 9, 12, 15])
SAFETY_BUFFER = 0.1          # cushion on worst-case HF
LIQUIDATION_THRESHOLD = 1.0
LTV_MAX = 0.65                # max possible LTV; stress test reduces effective LTV


def project_health_under_shock(
        pos: UniswapV3Position,
        initial_price: float,
        shock_pct: float,
        loan_amount: float,
        aave: AaveSimulator
) -> float:
    shocked_price = initial_price * (1 + shock_pct / 100)
    if shocked_price <= 0:
        return 0.0
    shocked_value = pos.compute_position_value(shocked_price)
    hf = aave.calculate_health_factor(shocked_value, loan_amount)
    return hf


def compute_worst_projected_hf(
        pos: UniswapV3Position,
        open_price: float,
        loan_amount: float,
        aave: AaveSimulator
) -> float:
    if loan_amount <= 0:
        return float('inf')
    projected_hfs = [
        project_health_under_shock(pos, open_price, shock, loan_amount, aave)
        for shock in SHOCK_LEVELS_PCT
    ]
    return min(projected_hfs) if projected_hfs else float('inf')


# ────────────────────────────────────────────────
# Main Simulation
# ────────────────────────────────────────────────

def run_hybrid_stress_simulation(
        output_dir_base: str = "../output/tradefi_adjusted",
        n_positions: int = N_POSITIONS
) -> Dict:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_dir = f"{output_dir_base}_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)

    price_df = load_historical_data()
    positions = prepare_positions_pool(n_positions)
    aave = AaveSimulator()

    timeseries = []
    total_liquidations_all = 0
    positions_ever_liquidated = set()

    print(f"Simulating {len(price_df)} days with {len(positions)} positions...")
    print(f"Output directory: {output_dir}")

    for idx, row in price_df.iterrows():
        date = row['date']
        open_price = float(row['open_price'])
        close_price = float(row['close_price'])
        price_change_pct = ((close_price - open_price) / open_price * 100) if open_price > 0 else 0.0

        daily_liquidations = 0
        liquidated_today = set()
        hf_values = []

        for pos in positions:
            pos_value_open = pos.compute_position_value(open_price)
            if pos_value_open <= 0:
                continue

            provisional_loan = aave.borrow(pos_value_open)

            # Stress test with provisional loan to estimate risk
            worst_hf = compute_worst_projected_hf(pos, open_price, provisional_loan, aave)

            # Adjust loan amount downward for stressed positions
            loan_amount = provisional_loan
            if worst_hf < float('inf') and worst_hf > 0:
                stress_factor = 1.0 / (worst_hf + SAFETY_BUFFER)
                safe_loan = pos_value_open * LTV_MAX / stress_factor
                loan_amount = min(provisional_loan, safe_loan)

            pos_value_close = pos.compute_position_value(close_price)
            actual_hf = aave.calculate_health_factor(pos_value_close, loan_amount)

            if actual_hf != float('inf'):
                hf_values.append(actual_hf)

            # Liquidation check (now benefits from reduced loan_amount)
            should_liquidate = actual_hf < LIQUIDATION_THRESHOLD

            if should_liquidate:
                daily_liquidations += 1
                liquidated_today.add(pos.position_id)
                positions_ever_liquidated.add(pos.position_id)

        avg_hf = np.mean(hf_values) if hf_values else float('inf')
        total_liquidations_all += daily_liquidations

        timeseries.append({
            'date': date,
            'open_price': open_price,
            'close_price': close_price,
            'price_change_pct': price_change_pct,
            'liquidations_tradfi_adjusted': daily_liquidations,
            'avg_health_factor': avg_hf,
            'worst_health_factor': worst_hf,
            'unique_liquidated_today': len(liquidated_today)
        })

        if idx % 100 == 0:
            print(f"{date.date()} | Liq: {daily_liquidations} | Avg HF: {avg_hf:.3f} | Worst HF: {worst_hf:.3f}")

    summary = {
        'total_dates': len(price_df),
        'total_positions': len(positions),
        'total_liquidations_all': total_liquidations_all,
        'unique_positions_ever_liquidated': len(positions_ever_liquidated),
        'avg_health_factor_all': np.mean([r['avg_health_factor'] for r in timeseries if r['avg_health_factor'] != float('inf')]),
        'wc_health_factor_all': np.mean([r['worst_health_factor'] for r in timeseries if r['worst_health_factor'] !=
                                         float('inf')]),
    }

    ts_df = pd.DataFrame(timeseries)
    ts_path = os.path.join(output_dir, "hybrid_adjusted_timeseries.csv")
    ts_df.to_csv(ts_path, index=False)
    print(f"Timeseries saved: {ts_path}")

    return {
        'timeseries_df': ts_df,
        'summary': summary,
        'output_dir': output_dir
    }


if __name__ == "__main__":
    result = run_hybrid_stress_simulation()
    print("\nSimulation Summary:")
    for k, v in result['summary'].items():
        print(f"  {k}: {v}")