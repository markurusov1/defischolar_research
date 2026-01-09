The **Liquidation Threshold** (along with other risk parameters like LTV and liquidation bonus) is assigned and 
managed by **Aave Governance**.

### How It Works
Aave is a decentralized protocol governed by the **Aave DAO** (Decentralized Autonomous Organization), where holders 
of the **AAVE token** propose, discuss, and vote on changes via **Aave Improvement Proposals (AIPs)**. Risk 
parameters are not set unilaterally by the Aave team or company—they require community approval through on-chain voting.  

- **Proposals** often come from risk service providers (e.g., Chaos Labs, Gauntlet) who analyze market data, 
  volatility, and liquidity to recommend adjustments. 
- Once a proposal passes voting, it updates the parameters on-chain for specific assets or markets (e.g., Ethereum 
  V3, Arbitrum). 
- This process ensures parameters reflect current risks while maintaining decentralization.

### Examples of Governance in Action
- Proposals have adjusted thresholds for assets like AAVE (e.g., increasing liquidation threshold from 73% to 76% on 
  Ethereum), ETH-correlated tokens, or newer listings. 
- For riskier or volatile collateral (e.g., certain LP positions if supported), thresholds are typically lower (e.g.,
  65-75%) to protect the protocol. 
- Safer assets (e.g., ETH, stablecoins) often have higher thresholds (up to 80-82%).

This governance model contrasts with centralized platforms but can lead to debates (as seen in late 2025 discussions 
about DAO vs. labs control). Parameters are public on the Aave app dashboard (app.aave.com/reserves) or docs, and as 
of early 2026, they continue to be tuned via active proposals.  

Liquidation Threshold of 70% is hypothetical for a conservative/riskier asset like a Uniswap v3. LP position—real 
thresholds vary by asset and market instance but are always set this way. 