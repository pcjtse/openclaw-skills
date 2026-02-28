---
name: Financial Research Expert
description: Runs a multi-tiered workflow to research companies, stocks, and macroeconomic trends using market data, SEC filings, and web intelligence. Use when: (1) User asks to research a company, stock, or ticker, (2) User wants fundamental analysis or investment context, (3) User asks about SEC filings, earnings, or regulatory disclosures, (4) User wants a professional research summary with a recommendation score. Covers: real-time market data and analyst sentiment (Tier 1), SEC 10-K/10-Q regulatory filings (Tier 2), and open-web macroeconomic and competitive intelligence (Tier 3).
---

# Financial Research Skill

This skill runs a structured, three-tier research workflow modeled on professional financial research platforms (Bloomberg → FactSet → Refinitiv → Open APIs), adapted to work with free custom tools.

## When to Use

Trigger this skill when:
- User asks to research a specific company, stock ticker, or sector
- User wants a fundamental analysis or investment thesis
- User asks about SEC filings, 10-K/10-Q reports, or regulatory disclosures
- User wants analyst sentiment, price targets, or recent news
- User asks for a final recommendation or conviction score on a stock

## Prerequisites

Before beginning any research, ensure the required dependencies are installed:
```bash
pip install -r scripts/requirements.txt
```

## How It Works

Always proceed through all three tiers systematically. Do not skip tiers unless explicitly requested by the user.

### Tier 1: Core Financial & Market Data (`scripts/stock_data.py`)

Gets the real-time or recent baseline for the target company/stock.

- **Purpose:** Gather quantitative context — pricing metrics, analyst sentiment, and breaking news
- **Provides:** Market Cap, P/E ratios, analyst upgrades/downgrades, recent news cycle

```bash
python scripts/stock_data.py <TICKER>
```

### Tier 2: Primary Source & Regulatory Filings (`scripts/sec_edgar.py`)

Dives into fundamental financial reporting directly from the source.

- **Purpose:** Download SEC 10-K (Annual) and 10-Q (Quarterly) filings for rigorous fundamental analysis
- **Provides:** MD&A insights, Risk Factors, detailed financial statements, and core business drivers

```bash
python scripts/sec_edgar.py <TICKER> --email <your-email> --company-name <your-identifier> --limit 1
```

Read the downloaded documents in the output directory (default: `./sec_filings`). Focus on Management's Discussion & Analysis (MD&A), Risk Factors, and financial statements.

### Tier 3: Open Market Intelligence & Sentiment (`scripts/web_search.py`)

Broadens scope once company-specific fundamentals are understood.

- **Purpose:** Gather macroeconomic context, competitor actions, and regulatory news not yet in structural reporting
- **Provides:** Real-world context clues to complement Tiers 1 and 2

```bash
python scripts/web_search.py "<your targeted research query>"
```

## Final Output Structure

Combine findings from all three tiers into a cohesive report:

1. **Executive Summary:** A high-level overview.
2. **Market & Analyst View (Tier 1):** Current metrics and sentiment.
3. **Fundamental Analysis (Tier 2):** Insights drawn directly from SEC filings.
4. **Broader Context & Risks (Tier 3):** External factors, competitors, and macroeconomic climate.
5. **Final Recommendation Score:** A score out of 10 indicating overall conviction/attractiveness of the investment, with a brief justification based on the prior analysis.
