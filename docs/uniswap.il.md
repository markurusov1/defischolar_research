## Depositing Liquidity in Uniswap V3: Asset Pair Dynamics and Impermanent Loss

When you deposit funds into a Uniswap V2 pool, you **must deposit both currencies** in the pair.

The proportion you must provide is determined by the **current ratio of the tokens already in the pool**. This ensures that your deposit does not change the market price of the assets at the moment you add liquidity.

### 1. The Ratio Rule

If you are adding liquidity to an existing pool, you must match the existing ratio of the two tokens (Token A and Token B). Mathematically, the proportion is:

**Example:**
Imagine an ETH/USDC pool where the current price is $3,000 per 1 ETH.

* **Pool Reserves:** 100 ETH and 300,000 USDC.
* **Your Deposit:** If you want to deposit **1 ETH**, you must also deposit **3,000 USDC**.
* **The Result:** You have maintained the 1:3,000 ratio, so the price remains unchanged.

### 2. What if you only have one token?

If you only have one of the two tokens (e.g., you have ETH but no USDC), you cannot add liquidity directly. You would first need to **swap 50%** of your ETH for USDC and then deposit both halves into the pool. Most modern interfaces or "Zaps" can automate this "swap and add" process for you in a single transaction.

### 3. What happens if you try to deposit a different ratio?

If you were to manually call the smart contract and provide a ratio different from the pool's current reserves:

* **Arbitrage:** You would effectively be offering one of the tokens at a "discount" compared to the market. Arbitrageurs would immediately swap against the pool to bring the price back to the market rate, causing you an instant loss.
* **Minting Logic:** Uniswap V2’s code is designed to give you Liquidity Provider (LP) tokens based on the *lesser* of the two amounts you provided relative to the pool ratio. This means if you over-deposit one asset, you don't get extra credit for it—you are essentially "donating" the excess to the existing liquidity providers.

### 4. Exception: The First Depositor

If you are the **very first person** to provide liquidity to a brand-new pool (creating the pool), you can deposit the two tokens in **any proportion you choose**.

* This initial deposit **sets the starting price** for that pool.
* If you set a price that is different from the global market rate (e.g., setting ETH at \$10,000 when it's actually 
  \$3,000), arbitrage bots will immediately trade against your pool to bring it to $3,000, resulting in a significant 
  loss of your initial funds

## Common Asset Pairs in Uniswap V3

When providing liquidity in Uniswap V3, the choice of asset pairs significantly influences the behavior of your liquidity position, particularly regarding impermanent loss (IL). While many liquidity providers (LPs) commonly use a "stablecoin + risky asset" pairing (e.g., USDC/ETH), it's essential to understand that the
Uniswap V3 protocol is permissionless and supports any pair of ERC-20 tokens.

In Uniswap V3, pools generally fall into one of three categories based on the relationship between the two assets:

### 1. Volatile / Stable (The "Classic" Pair)

* **Examples:** ETH/USDC, WBTC/DAI, LINK/USDT.
* **Dynamic:** This is what most people think of when they talk about "risky assets." One asset has a fixed value ($1.00), while the other fluctuates.
* **IL Profile:** Impermanent Loss occurs whenever the risky asset moves. If the risky asset doubles, your position rebalances toward the stablecoin.

### 2. Volatile / Volatile (The "Correlated" or "Cross" Pair)

* **Examples:** ETH/WBTC, ARB/ETH, PEPE/ETH.
* **Dynamic:** Both assets are risky. You are effectively betting on the **ratio** between them rather than their price in USD.
* **IL Profile:** IL only happens if the two assets **diverge**. If ETH and WBTC both go up by 10% against the dollar, the ratio stays the same, and you have **zero impermanent loss**. You only suffer IL if one outperforms the other significantly.

### 3. Stable / Stable (The "Pegged" Pair)

* **Examples:** USDC/USDT, DAI/USDC, stETH/ETH (technically "correlated" but behaves like a peg).
* **Dynamic:** Both assets aim to maintain the same value.
* **IL Profile:** These pools are popular for "Concentrated Liquidity" because you can set an extremely narrow range (e.g.,  to ). IL is nearly zero unless one of the assets "de-pegs" (loses its intended value).

---

### How V3 Fee Tiers Handle These Pairs

Uniswap V3 uses **Fee Tiers** to categorize these different types of risk. When you create or join a pool, you typically choose a fee based on how the assets behave:

| Fee Tier | Common Use Case | Why? |
| --- | --- | --- |
| **0.01% / 0.05%** | **Stable/Stable** | Low risk of IL; LPs accept lower fees for high volume. |
| **0.30%** | **ETH/Stable** | Standard "risky" pairs. Balances fee income with IL risk. |
| **1.00%** | **Exotic/Meme** | High risk of the asset crashing or diverging; LPs need high fees to offset IL. |

### Summary

You can pair **any** two tokens. The "Stablecoin + Risky" setup is just the most common because it’s the easiest way for traders to move in and out of positions and for LPs to measure their profit in "real-world" dollar terms.

## V2 Impermanent Loss
In Uniswap V2 (and other standard Constant Product Market Makers), the formula for Impermanent Loss is much simpler because liquidity is distributed uniformly from price $0$ to $\infty$.
The formula is expressed in terms of the price ratio ($r$), which is the ratio of the new price to the original price ($P_{new} / P_{initial}$).

#### The Standard V2 Formula

$IL = \frac{2\sqrt{r}}{1+r} - 1$

Where:
- $r$: The price change ratio (e.g., if the price doubles, $r = 2$; if it drops by half, $r = 0.5$)
- $IL$: The loss as a percentage (a result of $-0.05$ means a 5% loss compared to just holding the assets)

Why does it look like this?
This formula is derived from the difference between the Value of the LP Position and the Value of Holding (HODL):

- Value in Pool ($V_{pool}$): Because of the $x \cdot y = k$ formula, your assets rebalance as the price changes. The 
value of your position at a new price ratio $r$ is:
$V_{pool} = V_{initial} \cdot \sqrt{r}$

- Value of Holding ($V_{hodl}$): If you just held the 50/50 split of tokens, your value would be:
$V_{hodl} = V_{initial} \cdot \frac{1+r}{2}$

Dividing the two gives you the performance ratio:

$\frac{V_{pool}}{V_{hodl}} = \frac{2\sqrt{r}}{1+r}$
#### Example Visuals

| Price Change (r) | Impermanent Loss (V2) |
| --- | --- |
| 1.25x (25% increase) | -0.6% |
| 1.50x (50% increase) | -2.0% |
| 2.00x (100% increase) | -5.7% |
| 3.00x (200% increase) | -13.4% |
| 4.00x (300% increase) | -20.0% |
| 5.00x (400% increase) | -25.5% |

### Key Characteristics of V2 IL
- Always Negative: Unless the price returns exactly to where you started ($r=1$), you are always at a slight loss 
compared to holding. 
- Symmetrical (Log-wise): A doubling of price ($r=2$) results in the exact same IL as a halving of price ($r=0.5$). 
- Predictable: Unlike V3, where your IL depends on your specific "ticks" or price range, V2 IL is a universal curve that applies to every liquidity provider in the pool regardless of when they entered.

## V3 Impermanent Loss

In Uniswap V3, the concept of Impermanent Loss (IL) is significantly more complex than in V2 because of Concentrated Liquidity. While V2 spreads your capital from price $0$ to $\infty$, V3 allows you to provide liquidity within a specific range $[P_a, P_b]$.

This concentration acts like leverage. It earns you more fees when the price is in range, but it also speeds up your impermanent loss.

### The Core Formula
   The formula for Impermanent Loss in Uniswap V3 depends on whether the current price ($P$) is inside or outside your chosen range $[P_a, P_b]$.

#### The Relative Loss Equation
   If the price stays within the range $[P_a, P_b]$, the value of your liquidity position ($V_{pool}$) compared to just holding the original assets ($V_{hodl}$) is calculated by:

$IL = \frac{V_{pool}}{V_{hodl}} - 1$

To find $V_{pool}$, Uniswap V3 uses "virtual reserves" which treat your concentrated position as a slice of a much larger V2-style curve. 
The value of your position at price $P$ is:

$V_{pool}(P) = L \cdot (2\sqrt{P} - \sqrt{P_a} - \frac{P}{\sqrt{P_b}})$

Where:
- $L$ = Liquidity (the "k" of your specific range)
- $P$ = Current price of the asset
- $P_a$ = Lower bound of your range
- $P_b$ = Upper bound of your range.

### Why V3 IL is "Amplified"
   In Uniswap V2, a $2\times$ price move always results in exactly $5.7\%$ IL. In Uniswap V3, the narrower your range, the higher your "Effective Leverage."

- Full Range ($0$ to $\infty$): Same as V2 (Standard 5.7% for 2x move)
- Wide Range: Moderate acceleration of loss
- Narrow Range: Massive acceleration; can reach 100% loss of one asset quickly|

### The "All-In" Point
If the price moves outside your range:
- Above $P_b$: Your position is now 100% Stablecoins (or the quote asset). You have "sold" all your upside
- Below $P_a$: Your position is now 100% Risky Asset (e.g., ETH). You have "bought" all the way down.
At these points, your IL becomes "locked" in terms of asset composition until the price returns to the range.
### The Relationship with "Ticks"
   Uniswap V3 tracks these ranges using Ticks. Each tick represents a $0.01\%$ (1 basis point) price change.
   The price at any tick $i$ is defined as:

$P(i) = 1.0001^i$

When you set a range, you are essentially choosing two ticks. The closer those ticks are, the higher your $L$ (Liquidity) for a given dollar amount, and the steeper the IL curve becomes if the price deviates from your entry.
#### Summary Comparison Table

| Feature | Uniswap V2 | Uniswap V3 |
| --- | --- | --- |
| Capital Distribution | $0$ to $\infty$ | User-defined range \[P\_a, P\_b\] |
| IL Formula | $2\frac{\sqrt{d}}{1+d} - 1$ | Dependent on range width (Leveraged) |
| Asset Composition | Always holds both assets | Can become 100\% of one asset |
| Risk | Lower, but lower fees | Higher IL risk, but much higher fee potential |


## Liquidity Provision in Uniswap V3: Who Chooses the Ranges?

In Uniswap V3, **liquidity providers (LPs) individually choose the price ranges for their liquidity positions**. The pool itself does **not** pre-define any specific ranges—the protocol is designed to be flexible and permissionless, allowing each LP to customize their strategy based on their risk tolerance, market outlook, and fee-earning goals. This is the core innovation of V3's "concentrated liquidity" model, which contrasts with Uniswap V2 (and full-range V3 positions), where liquidity is spread uniformly across all possible prices.

### Key Details on How It Works
- **LP-Driven Customization**:
    - When an LP adds liquidity to a V3 pool (e.g., ETH/USDC), they specify a **price range** (defined by "ticks" in the protocol) where their capital will be active. For example, an LP bullish on ETH might choose a narrow range like $3,000–$3,500 USDC per ETH to concentrate capital for higher fees from trades in that band.
    - This range can be **any valid interval** within the pool's price bounds (from near 0 to very high values), as long as it aligns with the pool's tick spacing (a small granularity limit based on the fee tier, e.g., 10, 60, or 200 ticks apart for 0.05%, 0.30%, or 1% fees).
    - LPs can create multiple positions with different ranges in the same pool to diversify (e.g., one narrow for high fees, one wide for stability).

- **Pool's Role**:
    - The pool only enforces the **overall mechanics**: It aggregates all LPs' liquidity across their chosen ranges to facilitate trades via the constant product formula (adjusted for concentration). There's no central "pre-defined" range; the pool dynamically uses whatever liquidity is provided in the current price area.
    - If the current market price moves **in-range** for an LP's position, their liquidity earns fees proportionally. **Out-of-range**, it stops earning fees and behaves like holding one asset (increasing impermanent loss risk).

- **Trade-Offs for LPs**:
    - **Narrow ranges**: Higher capital efficiency (up to 4,000x vs. V2) and fees, but higher risk of going out-of-range and missing trades.
    - **Wide ranges**: More stable (approximates V2), but lower efficiency.
    - This choice is strategic: Risk-averse LPs opt for broader ranges, while active ones (e.g., market makers) use narrow ones and rebalance frequently.