from aave.aave_original import AaveSimulator
from uniswap.il_v3 import UniswapV3Position

if __name__ == "__main__":
    initial_eth_max = 3000.0
    initial_usdc_max = 2000.0

    sim = AaveSimulator()
    position_value = initial_eth_max+initial_usdc_max
    loan = sim.borrow(position_value)
    hf = sim.calculate_health_factor(position_value, loan)
    decision = sim.decide_liquidation(position_value, loan)

    print("Position value", position_value)
    print("Loan amount   ", loan)
    print("Health factor ", hf)
    print("Decision      ", decision)

    # Uniswap
    position = UniswapV3Position(
        initial_eth_max,
        initial_usdc_max,
        range_width=0.1
    )

    # Simulate a 10% price drop
    price_drop = 0.10
    new_price = position.initial_price * (1 - price_drop)
    print(f"\nAfter {price_drop * 100:.0f}% ETH price drop:")
    print(f"New price (USDC per ETH): {new_price:.4f}")

    position_value = position.compute_position_value(new_price)
    print(f"Pool position value at new price: {position_value:.2f} USDC")

    hold_value = position.compute_hold_value(new_price)
    print(f"Hold strategy value at new price: {hold_value:.2f} USDC")

    il = position.compute_impermanent_loss(new_price)
    print(f"Impermanent Loss: {il:.4f} or {il * 100:.2f}%")
