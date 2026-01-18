# hybrid_stress_sim.py
# Implements TradFi-style dynamic margin / stress-tested liquidation thresholds
# in a DeFi-style daily simulation loop over historical ETH prices

import os
import pandas as pd
import numpy as np
from typing import List, Dict
import docs.milestone_2.src.data_loader as data_loader

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
SHOCK_LEVELS_PCT = np.array([-15, -12, -9, -6, -3, 0, 3, 6, 9, 12, 15])
SAFETY_BUFFER = 0.10          # extra cushion on worst-case health factor
LIQUIDATION_THRESHOLD = 1.0   # health factor < 1.0 → liquidation eligible
LTV_MAX = 0.65                # same as AaveSimulator default


def project_health_under_shock(
        pos: UniswapV3Position,
        initial_price: float,
        shock_pct: float,
        loan_amount: float,
        aave: AaveSimulator
) -> float:
    """
    Project position value + health factor under one hypothetical price shock.
    Includes impermanent loss effect implicitly via recomputed position value.
    """
    shocked_price = initial_price * (1 + shock_pct / 100)
    if shocked_price <= 0:
        return 0.0

    # Recompute position value at shocked price (accounts for range / IL)
    shocked_value = pos.compute_position_value(shocked_price)

    # Health factor under this scenario
    hf = aave.calculate_health_factor(shocked_value, loan_amount)
    return hf


def compute_dynamic_threshold(
        pos: UniswapV3Position,
        open_price: float,
        loan_amount: float,
        aave: AaveSimulator
) -> float:
    """
    TradFi-style: find the WORST projected health factor across all shocks,
    then add a buffer → this becomes the liquidation trigger threshold for the day.
    """
    if loan_amount <= 0:
        return float('inf')

    projected_hfs = []
    for shock in SHOCK_LEVELS_PCT:
        hf_shock = project_health_under_shock(pos, open_price, shock, loan_amount, aave)
        projected_hfs.append(hf_shock)

    worst_hf = min(projected_hfs) if projected_hfs else float('inf')
    dynamic_threshold = worst_hf + SAFETY_BUFFER

    # Never let threshold go below liquidation point (safety)
    return max(dynamic_threshold, LIQUIDATION_THRESHOLD)


# ────────────────────────────────────────────────
# Step 2 + 3: Main Simulation Loop
# ────────────────────────────────────────────────

def run_hybrid_stress_simulation(
        output_dir: str = "output_hybrid",
        n_positions: int = N_POSITIONS
) -> Dict:
    os.makedirs(output_dir, exist_ok=True)

    # Load data & prepare positions (Step 1)
    price_df = load_historical_data()
    positions = prepare_positions_pool(n_positions)
    aave = AaveSimulator()  # fresh simulator instance

    timeseries = []
    total_liquidations_all = 0
    positions_ever_liquidated = set()

    print(f"Simulating {len(price_df)} days with {len(positions)} positions...")

    # Outer loop: each historical date (Step 2)
    for idx, row in price_df.iterrows():
        date = row['date']
        open_price = float(row['open_price'])
        close_price = float(row['close_price'])
        price_change_pct = ((close_price - open_price) / open_price * 100) if open_price > 0 else 0.0

        daily_liquidations = 0
        liquidated_today = set()
        hf_values = []

        # Inner loop: each position (Step 3)
        for pos in positions:
            # ── Phase A: Value & borrow at OPEN price ──
            pos_value_open = pos.compute_position_value(open_price)
            if pos_value_open <= 0:
                continue

            loan_amount = aave.borrow(pos_value_open)  # LTV_MAX * value

            # ── Phase B: TradFi stress test → set DYNAMIC threshold for this day ──
            dynamic_threshold = compute_dynamic_threshold(
                pos, open_price, loan_amount, aave
            )

            # ── Phase C: Realized outcome at CLOSE price ──
            pos_value_close = pos.compute_position_value(close_price)
            actual_hf = aave.calculate_health_factor(pos_value_close, loan_amount)

            # Record health factor (for stats)
            if actual_hf != float('inf'):
                hf_values.append(actual_hf)

            # ── Decision: Liquidate if actual HF < dynamic threshold ──
            should_liquidate = actual_hf < dynamic_threshold

            if should_liquidate:
                daily_liquidations += 1
                liquidated_today.add(pos.position_id)   # assuming position has .position_id
                positions_ever_liquidated.add(pos.position_id)

        # ── Daily summary ──
        avg_hf = np.mean(hf_values) if hf_values else float('inf')
        total_liquidations_all += daily_liquidations

        timeseries.append({
            'date': date,
            'open_price': open_price,
            'close_price': close_price,
            'price_change_pct': price_change_pct,
            'liquidations_tradfi': daily_liquidations,
            'avg_health_factor': avg_hf,
            'unique_liquidated_today': len(liquidated_today)
        })

        if idx % 100 == 0:
            print(f"{date.date()} | Liq: {daily_liquidations} | Avg HF: {avg_hf:.3f}")

    # ── Final summary ──
    summary = {
        'total_dates': len(price_df),
        'total_positions': len(positions),
        'total_liquidations_all': total_liquidations_all,
        'unique_positions_ever_liquidated': len(positions_ever_liquidated),
        'avg_health_factor_all': np.mean([r['avg_health_factor'] for r in timeseries if r['avg_health_factor'] != float('inf')]),
    }

    # Save timeseries
    ts_df = pd.DataFrame(timeseries)
    ts_path = os.path.join(output_dir, "hybrid_timeseries.csv")
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