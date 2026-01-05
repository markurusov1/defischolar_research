# DeFiScholar Research Repository

**Research materials, data, and scripts for defischolar.com**

This repository supports a beginner-friendly high school research project titled:  
**"Why Do DeFi Liquidity Providers Get Liquidated So Often? A Comparison with Traditional Market Makers"**

The project compares fixed Loan-to-Value (LTV) liquidation models in DeFi lending protocols (e.g., Aave, Compound) with dynamic, risk-based portfolio margin models in Traditional Finance (TradFi, e.g., used by firms like Jane Street and Citadel). It focuses on Uniswap v3 liquidity provider (LP) positions as collateral, highlighting how impermanent loss (IL) contributes to high liquidation rates in DeFi—and how TradFi-inspired stress-testing could reduce them by 95–99%.

### Project Goals
- Analyze real-world DeFi liquidation events (e.g., FTX 2022, market dips in 2025).
- Simulate fixed LTV vs. hypothetical risk-based margins using historical data.
- Propose improvements: dynamic, IL-aware LTV for safer leverage (5–10x) and higher TVL/fees in Uniswap.
- Produce a 10–15 page research paper with charts, aimed at competitions like Regeneron STS, JSHS, or Davidson Fellows.

### Milestones
1. Foundations & Literature Review
2. Data Collection & Basic Analysis
3. Simulations & Charts  
4. Writing, revisions, and final paper

### Repository Structure
```
defischolar_research/
├── docs/
│   └── milestone_1/          # Materials from Weeks 1–2 (literature review, summaries, comparison tables)
│       ├── (SEC paper.md, comparison tables, Uniswap v3 notes, etc.)
├── data/                     # Raw and processed datasets (to be added)
│   ├── historical_prices/    # ETH/USDC Uniswap v3 pool data (CSV from Dune/Flipside)
│   └── liquidation_events/   # DeFi liquidation data
├── notebooks/                # Jupyter notebooks for analysis and simulations
│   └── simulations.ipynb     # Fixed LTV vs. risk-based models, charts
├── scripts/                  # Python scripts for data pulling and processing
├── paper/                    # Final research paper drafts (Overleaf exports or Markdown)
│   └── defi_liquidations_paper.pdf (or .tex/.md)
├── images/                   # Screenshots, charts, and visuals (e.g., from project summaries)
└── README.md                 # This file
```

*(Current status: Early stage – primarily docs/milestone_1 populated with literature notes. More folders/files will be added as the project progresses.)*

### Key Resources & References
- **Uniswap v3 Whitepaper** → Concentrated liquidity and impermanent loss.
- **SEC Portfolio Margin Rule (2006)** → Risk-based stress testing.
- **Darrell Duffie’s Work** → Risk-based haircuts and procyclicality.
- Data sources: Dune Analytics, Flipside Crypto, CME/SEC reports.

### How to Contribute or Follow
This is a solo high school research project, but feel free to star/watch for updates! Issues can be opened for suggestions.

For more details, visit [defischolar.com](http://defischolar.com) (project website in development).

**License**: MIT License (feel free to reuse for educational purposes).

*Last updated: January 2026*