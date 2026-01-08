## Liquidation Threshold (LT) in DeFi

The Liquidation Threshold (LT) is a critical risk parameter in protocols like Aave that determines when a borrow 
position becomes undercollateralized. Expressed as a percentage (e.g., $70\%$), it represents the maximum 
debt-to-collateral ratio allowed before the protocol triggers a liquidation to protect lenders.  

### The Health Factor ($HF$) Formula

Aave monitors the safety of a position by calculating a Health Factor. For a single collateral asset, the formula is:

$$HF = \frac{V_{c} \times LT}{V_{d}}$$

Where:
- $V_{c}$ is the Value of Collateral
- $LT$ is the Liquidation Threshold
- $V_{d}$ is the Value of Debt (Borrowed Amount)

#### Status Conditions:
If $HF \geq 1$: The position is healthy.
If $HF < 1$: The position is eligible for liquidation.

### LT vs. Loan-to-Value (LTV)
It is important to distinguish between the initial borrowing limit and the liquidation limit:
#### **LTV** 

LTV (e.g., $65\%$): Defines the maximum amount a user can borrow at the moment they open a position ($V_{d} 
\leq V_{c} \times LTV$).
#### Liquidation Threshold 

Liquidation Threshold (e.g., $70\%$): A higher ceiling that acts as a safety buffer. It allows for market volatility 
or interest Accrual after the loan is taken. The gap between LTV and LT (e.g., $5\%$) gives borrowers a "cushion" to 
add collateral or repay debt before facing a liquidation event.

### Example Scenario
Using a Uniswap LP position as collateral:
1. Initial State
   - $V_{c} = \$6,000$
   - $V_{d} = \$3,500$
   - $LT = 0.70$
   
   $$HF = \frac{6,000 \times 0.70}{3,500} = \frac{4,200}{3,500} = 1.20 \quad (\text{Safe})$$

3. After a Market Drop
   If the collateral value falls to $\$4,984$ due to price action or impermanent loss:
   $$HF = \frac{4,984 \times 0.70}{3,500} \approx \frac{3,488.8}{3,500} \approx 0.9968$$
   Since $HF < 1$, the position is now eligible for liquidation.

### Risk Implications
Conservative Assets: Stablecoins or ETH often have a high $LT$ (e.g., $82\%$), allowing for higher capital efficiency.
Volatile Assets: Riskier collateral like Uniswap v3 LP positions have a lower $LT$ (e.g., $70\%$) to account for 
rapid price swings and liquidity slippage. 
