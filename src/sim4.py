# hybrid_stress_sim.py
# Hybrid DeFi + TradFi stress simulation with optional regression-based projection mode
# Regression mode aims for low liquidations (like stress_testing.py ~88 total)

import os
from datetime import datetime
from typing import List, Dict

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from aave.aave_original import AaveSimulator
# ────────────────────────────────────────────────
# Import your existing modules
# ────────────────────────────────────────────────
from position_loader import create_positions, N_POSITIONS
from uniswap.il_v3 import UniswapV3Position

# ────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────
REGRESSION_MODE = True  # True → use regression + IL adj for projections (low liqs)
# False → direct per-position value recompute (current/high liqs)
IL_ADJUST_FACTOR = 0.5  # Scale for IL impact in regression mode (0.3-0.7 typical)
HISTORICAL_CSV_PATH = "../output/run_20260111_122829/liquidation_timeseries.csv"  # Adjust to your actual file
# path/name

SHOCK_LEVELS_PCT = np.array([-15, -12, -9, -6, -3, 0, 3, 6, 9, 12, 15])
SAFETY_BUFFER = 0.6  # cushion (higher = less de-leveraging)
LIQUIDATION_THRESHOLD = 1.0
LTV_MAX = 0.65


def load_historical_data() -> pd.DataFrame:
    try:
        import data_loader
        df = data_loader.df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        return df[['date', 'open_price', 'close_price']]
    except Exception as e:
        raise RuntimeError("Could not load price data from data_loader") from e


def prepare_positions_pool(n_positions: int = N_POSITIONS) -> List[UniswapV3Position]:
    return create_positions(n_positions=n_positions)


def project_health_under_shock(
        pos: UniswapV3Position,
        initial_price: float,
        shock_pct: float,
        loan_amount: float,
        aave: AaveSimulator,
        model: LinearRegression = None
) -> float:
    shocked_price = initial_price * (1 + shock_pct / 100)
    if shocked_price <= 0:
        return 0.0

    if REGRESSION_MODE and model is not None:
        # Regression baseline prediction for this shock
        reg_pred = model.predict([[shock_pct]])[0]

        # Per-position impermanent loss (negative = loss)
        il = pos.compute_impermanent_loss(shocked_price)

        # Adjust HF downward by scaled IL
        adjusted_hf = reg_pred + (il * IL_ADJUST_FACTOR)
        return max(adjusted_hf, 0.0)
    else:
        # Direct recompute (original mode)
        shocked_value = pos.compute_position_value(shocked_price)
        return aave.calculate_health_factor(shocked_value, loan_amount)


def compute_worst_projected_hf(
        pos: UniswapV3Position,
        open_price: float,
        loan_amount: float,
        aave: AaveSimulator,
        model: LinearRegression = None
) -> float:
    if loan_amount <= 0:
        return float('inf')
    projected_hfs = [
        project_health_under_shock(pos, open_price, shock, loan_amount, aave, model)
        for shock in SHOCK_LEVELS_PCT
    ]
    return min(projected_hfs) if projected_hfs else float('inf')


def run_hybrid_stress_simulation(
        output_dir_base: str = "../output/tradefi_adjusted",
        n_positions: int = N_POSITIONS
) -> Dict:
    global REGRESSION_MODE
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_dir = f"{output_dir_base}_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)

    price_df = load_historical_data()
    positions = prepare_positions_pool(n_positions)
    aave = AaveSimulator()

    # Fit regression model if in REGRESSION_MODE
    model = None
    if REGRESSION_MODE:
        try:
            hist_df = pd.read_csv(HISTORICAL_CSV_PATH)
            hist_df = hist_df.dropna(subset=['price_change', 'average_health_factor'])  # adjust column names if needed
            print("Model data read from CSV:" + HISTORICAL_CSV_PATH)

            X = hist_df['price_change'].values.reshape(-1, 1)  # or 'price_change'
            y = hist_df['average_health_factor'].values
            model = LinearRegression()
            # extra safety
            y = y[np.isfinite(y)]
            X = X[np.isfinite(y)]
            #
            model.fit(X, y)
            print(f"R² score: {model.score(X, y):.4f}")
            print(f"Regression model fitted: slope={model.coef_[0]:.4f}, intercept={model.intercept_:.4f}")
            print(f"Training rows used: {len(X)}")
        except Exception as e:
            print(f"Warning: Could not fit regression model from {HISTORICAL_CSV_PATH}: {e}")
            print("Falling back to direct mode for this run.")
            REGRESSION_MODE = False  # disable if fit fails

    timeseries = []
    total_liquidations_all = 0
    positions_ever_liquidated = set()

    print(f"Simulating {len(price_df)} days with {len(positions)} positions...")
    print(f"Output directory: {output_dir}")
    print(f"Mode: {'Regression + IL adj' if REGRESSION_MODE else 'Direct per-position'}")

    for idx, row in price_df.iterrows():
        date = row['date']
        open_price = float(row['open_price'])
        close_price = float(row['close_price'])
        price_change_pct = ((close_price - open_price) / open_price * 100) if open_price > 0 else 0.0

        daily_liquidations = 0
        liquidated_today = set()
        hf_values = []
        daily_ltvs = []                  # for avg effective LTV
        reductions_applied = 0           # count of positions reduced

        for pos in positions:
            pos_value_open = pos.compute_position_value(open_price)
            if pos_value_open <= 0:
                continue

            provisional_loan = aave.borrow(pos_value_open)

            # Stress test → worst projected HF
            worst_hf = compute_worst_projected_hf(pos, open_price, provisional_loan, aave, model)

            # Adjust loan downward if stressed
            loan_amount = provisional_loan
            if worst_hf < float('inf') and worst_hf > 0:

                max_allowed_ltv = LTV_MAX
                if worst_hf < 1.2:
                    max_allowed_ltv = 0.55
                elif worst_hf < 1.0:
                    max_allowed_ltv = 0.45
                elif worst_hf < 0.8:
                    max_allowed_ltv = 0.35

                sliding_safe_loan = pos_value_open * max_allowed_ltv

                stress_factor = 1.0 / (worst_hf + SAFETY_BUFFER)
                stress_safe_loan = pos_value_open * LTV_MAX / stress_factor

                safe_loan = min(sliding_safe_loan, stress_safe_loan)
                loan_amount = min(provisional_loan, safe_loan)

            # Log effective LTV and reduction
            effective_ltv = min(max(loan_amount / pos_value_open if pos_value_open > 0 else 0, 0), 1)
            daily_ltvs.append(effective_ltv)
            if loan_amount < provisional_loan:
                reductions_applied += 1

            pos_value_close = pos.compute_position_value(close_price)
            actual_hf = aave.calculate_health_factor(pos_value_close, loan_amount)

            if actual_hf != float('inf'):
                hf_values.append(actual_hf)

            should_liquidate = actual_hf < LIQUIDATION_THRESHOLD

            if should_liquidate:
                daily_liquidations += 1
                liquidated_today.add(pos.position_id)
                positions_ever_liquidated.add(pos.position_id)

        avg_hf = np.mean(hf_values) if hf_values else float('inf')
        avg_ltv = np.mean(daily_ltvs) if daily_ltvs else 0.0
        total_liquidations_all += daily_liquidations

        timeseries.append({
            'date': date,
            'open_price': open_price,
            'close_price': close_price,
            'price_change_pct': price_change_pct,
            'liquidations_tradfi_adjusted': daily_liquidations,
            'avg_health_factor': avg_hf,
            'avg_effective_ltv': avg_ltv,
            'reductions_applied_today': reductions_applied,
            'unique_liquidated_today': len(liquidated_today)
        })

        if idx % 100 == 0:
            print(f"{date.date()} | Liq: {daily_liquidations} | Avg HF: {avg_hf:.3f} | Avg LTV: {avg_ltv:.3f} | Reductions: {reductions_applied}")

    summary = {
        'total_dates': len(price_df),
        'total_positions': len(positions),
        'total_liquidations_all': total_liquidations_all,
        'unique_positions_ever_liquidated': len(positions_ever_liquidated),
        'avg_health_factor_all': np.mean([r['avg_health_factor'] for r in timeseries if r['avg_health_factor'] != float('inf')]),
        'avg_effective_ltv_all': np.mean([r['avg_effective_ltv'] for r in timeseries]),
        'total_reductions_applied': sum(r['reductions_applied_today'] for r in timeseries),
    }

    ts_df = pd.DataFrame(timeseries)
    ts_path = os.path.join(output_dir, "hybrid_adjusted_timeseries.csv")
    ts_df.to_csv(ts_path, index=False)

    print(f"Timeseries saved: {ts_path}")
    # Print summary to console
    print("\n===== SIMULATION SUMMARY =====")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    # Save summary to file next to CSV
    summary_path = os.path.join(output_dir, "summary.txt")
    with open(summary_path, 'w') as f:
        f.write("===== SIMULATION SUMMARY =====\n")
        for k, v in summary.items():
            f.write(f"{k}: {v}\n")
    print(f"Summary saved to: {summary_path}")
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
