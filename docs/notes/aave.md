## Liquidation Threshold (LT) in DeFi

The Liquidation Threshold (LT) is a critical risk parameter in protocols like Aave that determines when a borrow 
position becomes undercollateralized. Expressed as a percentage (e.g., $70\%$), it represents the maximum 
debt-to-collateral ratio allowed before the protocol triggers a liquidation to protect lenders.  

### The Health Factor ($HF$) Formula

Aave monitors the safety of a position by calculating a Health Factor. For a single collateral asset, the formula is:

$HF = \frac{V_{c} \times LT}{V_{d}}$

Where:
- $V_{c}$ is the Value of Collateral
- $LT$ is the Liquidation Threshold
- $V_{d}$ is the Value of Debt (Borrowed Amount)

#### Status Conditions:
If $HF \geq 1$: The position is healthy.
If $HF < 1$: The position is eligible for liquidation.

### Liquidation Threshold 

A Liquidation Threshold of 0.70 (70%) means the protocol considers the loan unsafe when the borrowed amount reaches more than 70% of the collateral's current market value. 
In other words:

The debt can grow (or collateral shrink) until Debt = 70% of Collateral → HF approaches 1.
Once Debt > 70% of Collateral → HF < 1 → Liquidation eligible.

This provides a safety buffer beyond the initial borrowing limit.

[read more on how Aave assigns LT value](aave.governance.md)
### Liquidation Threshold vs. Loan-to-Value (LTV)
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
   
   $HF = \frac{6,000 \times 0.70}{3,500} = \frac{4,200}{3,500} = 1.20 \quad (\text{Safe})$

2. After a Market Drop
   If the collateral value falls to \$4,984 due to price action or impermanent loss:

   $HF = \frac{4,984 \times 0.70}{3,500} \approx \frac{3,488.8}{3,500} \approx 0.9968$
   
   Since $HF < 1$, the position is now eligible for liquidation.

### Risk Implications
Conservative Assets: Stablecoins or ETH often have a high $LT$ (e.g., 82%), allowing for higher capital efficiency.
Volatile Assets: Riskier collateral like Uniswap v3 LP positions have a lower $LT$ (e.g., 70%) to account for 
rapid price swings and liquidity slippage. 

## Loss
When a position is eligible for liquidation, you do **not** lose everything, but you lose significantly more than 
just the "amount of the loan." 

Think of liquidation as a forced sale where the protocol pays off your debt using your collateral, but it charges 
you a "tip" or penalty to reward the person (liquidator) who does the work. 

### What do you lose?

In a typical liquidation event (like on Aave), you lose:

1. **The Repaid Debt:** A portion of your collateral is taken to pay back the borrowed amount.
2. **The Liquidation Bonus (The "Penalty"):** This is the extra amount you lose on top of the debt. It typically 
   ranges from **5% to 15%** of the liquidated value, depending on the asset's risk. 

### Is it a total loss?

**No.** Lending protocols are designed to be "partial" and "fair" where possible.

* **Partial Liquidation:** In Aave v3, typically only **50%** of your debt is liquidated at once. The goal is to 
  bring your Health Factor back above 1.0, not to wipe you out. 
* **Remaining Collateral:** After the debt is repaid and the penalty is taken, any leftover collateral remains in 
  your account. 

---

### Comparison: Debt vs. Total Loss

Let's look at your previous Uniswap LP example to see the math:

* **Collateral:** $4,984
* **Debt:** $3,500
* **Liquidation Bonus:** 10% (for a risky LP position)

If a liquidator steps in to repay **50%** of your debt ($1,750):

* **Debt Repaid:** $1,750
* **Bonus to Liquidator ():** $175
* **Total Collateral Taken:** $1,750 + $175 = **$1,925**

**Your New Position:**

* **Remaining Collateral:** $4,984 - $1,925 = **$3,059**
* **Remaining Debt:** $3,500 - $1,750 = **$1,750**
* **New Health Factor:**  (You are now safe again, but you "lost" $175 in the process).

### When would you lose "Everything"?

You only lose 100% of your collateral if:

1. **The Market Crashes Too Fast:** If the value of your collateral drops so quickly that it becomes worth *less* 
   than the debt you owe, the protocol will take 100% of the collateral to cover as much debt as possible (this is 
   called **Bad Debt**).  
2. **Full Liquidation:** Some protocols (or specific conditions in Aave v3, like very small positions or a Health 
   Factor below 0.95) allow for **100%** of the debt to be liquidated in one go. 

### Illustrative Example:

This simulation shows exactly what happens to your $6,000 Uniswap LP position as the market price drops.Liquidation Simulation Table

#### Assumptions:
- Liquidation Threshold (LT): 70%
- Liquidation Bonus (Penalty): 10%
- Close Factor: 50% (The protocol liquidates half your debt to restore health)

#### Key Takeaways from the Math
1. The "Extra" Loss (The Penalty): when the 17% drop occurs, your $HF$ falls to 0.996. A liquidator repays 1,750 (half your debt). However, you don't just lose $1,750 of collateral. 
2. You lose: $\text{Debt Repaid} + \text{Liquidation Bonus} = \$1,750 + (10\% \times \$1,750) = \$1,925$
3. The $175 is the "penalty"—this is the value that vanishes from your pocket and goes to the liquidator as a reward. 
4. The "Safety Reset" Notice that after the liquidation at a 17% drop, your New Health Factor would jump from 0.
   99 back up to $\approx$ 1.22
- **Before:** $\frac{\$4,980 \times 0.70}{\$3,500} = 0.99$
- **After:** $\frac{\$3,055 \times 0.70}{\$1,750} = 1.22$
- The protocol intentionally takes enough collateral to make your remaining position "safe" again, preventing a 
continuous loop of liquidations
5. Impact of Larger Drops: As the price drops further, the amount you lose increases because your Health Factor 
   drops more, triggering larger liquidations. At a 30% drop, your New Health Factor after the first liquidation 
   is only 0.91, meaning you are still undercollateralized and at risk of another liquidation.
6. Why You Don't Lose "Everything" – unless the price of your collateral crashes to zero instantly, you are left with 
the remaining collateral ($3,055 in the 17% drop scenario). You still own that asset; it is just a smaller 
   amount than you started with

#### Summary
You lose the portion of collateral needed to pay the debt PLUS a 5-15% penalty fee. You only lose "everything" if 
the collateral value drops so fast that it can no longer cover the debt (becoming "Bad Debt").