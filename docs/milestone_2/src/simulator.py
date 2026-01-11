from position_loader import create_positions
from typing import Dict, Tuple

# -------------------  Define crashes to analyze -------------------
crashes = {
    'May 2021 Crash': ('2021-05-01', '2021-06-30'),
    'FTX Nov 2022': ('2022-11-01', '2022-11-30'),
}


def prepare_positions(n_positions: int = 500):
    """Create positions and return a list."""
    positions = create_positions(n_positions=n_positions)
    return positions


def load_price_df():
    """Load the price dataframe from data_loader.py (must expose df).
    Raises RuntimeError if data_loader is not available or df is missing.
    """
    try:
        import data_loader
        price_df = data_loader.df
        return price_df
    except Exception as e:
        raise RuntimeError("data_loader.py must exist and expose a dataframe `df` with 'date' and 'price' columns") from e


def prepare_aave_simulator():
    """Instantiate and return an AaveSimulator."""
    from aave.aave_original import AaveSimulator
    return AaveSimulator()


def initialize_loans(lender, positions, price_df) -> Tuple[Dict[str, float], Dict[str, object]]:
    """Compute initial loan amounts for each position based on its initial price.

    Returns:
        position_loans: dict mapping position id -> loan amount
        position_objs: dict mapping position id -> position object
    """
    position_loans = {}
    position_objs = {}

    for i, pos in enumerate(positions):
        pos_id = f"id#{i}"
        # Compute the initial position value using the position's initial price if available,
        # otherwise fall back to data_loader first price
        initial_price = getattr(pos, 'initial_price', None)
        if initial_price is None:
            initial_price = float(price_df.iloc[0]['price'])
        pos_value = pos.compute_position_value(initial_price)
        loan_amount = lender.borrow(pos_value)
        position_loans[pos_id] = loan_amount
        position_objs[pos_id] = pos

    return position_loans, position_objs


def run_full_simulation(sim, position_loans, position_objs, price_df) -> Dict:
    """Run simulation over all dates in the price dataframe.

    Returns a dict with:
        - timeseries: list of dicts, one per date with:
            {date, price, total_liquidations, unique_liquidated, avg_health_factor}
        - summary: dict with aggregate stats over all dates
    """
    timeseries = []

    total_liquidations_all = 0
    total_dates = 0
    hf_sum_all = 0.0
    hf_count_all = 0
    positions_ever_liquidated = set()

    for _, row in price_df.iterrows():
        date = row['date']
        price = float(row['price'])

        total_liquidations_day = 0
        liquidated_today = set()
        hf_sum_day = 0.0
        hf_count_day = 0

        for pid, pos in position_objs.items():
            pos_value = pos.compute_position_value(price)
            loan = position_loans[pid]

            decision = sim.decide_liquidation(pos_value, loan)
            hf = decision.get('health_factor', float('inf'))

            if hf != float('inf'):
                hf_sum_day += hf
                hf_count_day += 1
                hf_sum_all += hf
                hf_count_all += 1

            if decision.get('should_liquidate'):
                total_liquidations_day += 1
                total_liquidations_all += 1
                liquidated_today.add(pid)
                positions_ever_liquidated.add(pid)

        avg_hf_day = (hf_sum_day / hf_count_day) if hf_count_day > 0 else float('inf')

        timeseries.append({
            'date': date,
            'price': price,
            'total_liquidations': total_liquidations_day,
            'unique_liquidated': len(liquidated_today),
            'avg_health_factor': avg_hf_day,
        })

        total_dates += 1

    avg_hf_all = (hf_sum_all / hf_count_all) if hf_count_all > 0 else float('inf')

    summary = {
        'total_dates': total_dates,
        'total_positions': len(position_objs),
        'total_liquidations_all': total_liquidations_all,
        'unique_positions_ever_liquidated': len(positions_ever_liquidated),
        'avg_health_factor_all': avg_hf_all,
    }

    return {
        'timeseries': timeseries,
        'summary': summary,
    }


def run_simulation(n_positions: int = 500):
    """High-level entrypoint: create positions, load prices, and run full historical simulation.

    Returns a dict with timeseries and summary stats.
    """
    #Open all positions
    positions = prepare_positions(n_positions=n_positions)

    # Load historical data
    price_df = load_price_df()

    #Setup Aave Lending Simulator
    lender = prepare_aave_simulator()

    #Borrow money against opened positions
    position_loans, position_objs = initialize_loans(lender, positions, price_df)

    #Run simulation over all dates and all positions
    result = run_full_simulation(lender, position_loans, position_objs, price_df)

    return result


if __name__ == "__main__":
    result = run_simulation(n_positions=500)

    summary = result['summary']
    timeseries = result['timeseries']

    print("\n===== SIMULATION SUMMARY =====")
    print(f"Total dates simulated: {summary['total_dates']}")
    print(f"Total positions: {summary['total_positions']}")
    print(f"Total liquidation events (all dates): {summary['total_liquidations_all']}")
    print(f"Unique positions ever liquidated: {summary['unique_positions_ever_liquidated']}")
    print(f"Average health factor (all): {summary['avg_health_factor_all']:.4f}")

    print("\n===== FIRST 10 DATES =====")
    for i, row in enumerate(timeseries[:10]):
        print(f"{i}: {row['date']} | price={row['price']:.2f} | liq={row['total_liquidations']} | unique_liq={row['unique_liquidated']} | hf={row['avg_health_factor']:.4f}")

    print("\n===== LAST 10 DATES =====")
    for i, row in enumerate(timeseries[-10:]):
        print(f"{i}: {row['date']} | price={row['price']:.2f} | liq={row['total_liquidations']} | unique_liq={row['unique_liquidated']} | hf={row['avg_health_factor']:.4f}")

    # Optional: print dates with highest liquidations
    top_liq_days = sorted(timeseries, key=lambda x: x['total_liquidations'], reverse=True)[:5]
    print("\n===== TOP 5 LIQUIDATION DAYS =====")
    for row in top_liq_days:
        print(f"{row['date']} | price={row['price']:.2f} | liq={row['total_liquidations']} | unique_liq={row['unique_liquidated']} | hf={row['avg_health_factor']:.4f}")


# -------------------  Notes -------------------
# This is a minimal, import-friendly simulator; it:
# - creates positions and loans once (loan is based on initial position value)
# - iterates over ALL historical prices in the price dataframe
# - recomputes position value at each price and calls the AaveSimulator to decide
#   whether that position would be liquidatable at the current value/loan
# - accumulates timeseries of liquidation events and health factors per date
# - produces summary stats: total liquidations, unique positions liquidated, avg HF
#
# Next steps / improvements:
# - update loan amounts after partial liquidations
# - include interest accrual over time
# - parallelize loops for speed
# - persist detailed per-position time series to CSV or a DB
