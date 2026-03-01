# OpenClaw Financial Research Skills

This repository contains financial research skills, scripts, and generated reports designed to work with **[OpenClaw](https://openclaw.ai)** — an AI-powered research and analysis assistant. These skills follow a professional, tiered research workflow inspired by institutional platforms like Bloomberg, FactSet, and Refinitiv, replicated entirely using free, open-source data sources.

---

## Repository Structure

```
.
├── financial-services-skills/
│   ├── SKILL.md                  # Core skill definition and workflow instructions
│   └── scripts/
│       ├── stock_data.py         # Tier 1: Market data, news & analyst sentiment (yfinance)
│       ├── sec_edgar.py          # Tier 2: SEC 10-K / 10-Q filing downloads (EDGAR)
│       ├── web_search.py         # Tier 3: General open web search (DuckDuckGo)
│       └── requirements.txt      # Python dependencies
├── technical-analysis-skills/
│   ├── SKILL.md                  # Trading agent skill & orchestration instructions
│   └── scripts/
│       ├── fetch_market_data.py    # Phase 1: Bulk OHLCV data fetching
│       ├── calculate_indicators.py # Phase 1: SMA, Bollinger, Donchian channels
│       ├── check_index_filter.py   # Phase 2: Market regime (bull/bear) filter
│       ├── apply_*.py              # Phase 3: Strategy signal generation
│       └── trading_agent_loop.py   # Phase 5: Full orchestration loop
├── MSFT_Research_Report.md       # Example output: Microsoft
```

---

## Getting Started

### Prerequisites

Ensure Python 3.9+ is installed, then install the required dependencies:

```bash
pip install -r financial-services-skills/scripts/requirements.txt
```

### Individual Script Usage

**Stock Market Data & Analyst Insights (Tier 1)**
```bash
python financial-services-skills/scripts/stock_data.py <TICKER>

# Examples:
python financial-services-skills/scripts/stock_data.py AAPL
python financial-services-skills/scripts/stock_data.py SHOP.TO
```

**SEC EDGAR Filings Downloader (Tier 2)**
```bash
python financial-services-skills/scripts/sec_edgar.py <TICKER> --email your@email.com --company-name "Your Name"

# Example:
python financial-services-skills/scripts/sec_edgar.py MSFT --email research@example.com --company-name "Research"
```

**General Web Search (Tier 3)**
```bash
python financial-services-skills/scripts/web_search.py <search query>

# Example:
python financial-services-skills/scripts/web_search.py "impact of AI regulations on big tech"
```

**Technical Analysis & Momentum Strategy (Trading Agent)**
```bash
# Run the full trading agent loop (Orchestration)
python technical-analysis-skills/scripts/trading_agent_loop.py --universe universe.csv --capital 100000 --strategy bollinger

# Individual Phase: Market Regime Filter
python technical-analysis-skills/scripts/check_index_filter.py --index ^GSPC --period 75

# Individual Phase: 20% Flipper Strategy
python technical-analysis-skills/scripts/apply_20percent_flipper.py indicators.csv --stop-pct 20
```

---

## Using with OpenClaw

This skill is designed to be used with **OpenClaw**. Once installed, you can invoke the financial research workflow using natural language prompts. OpenClaw reads the `SKILL.md` to understand the research process and automatically orchestrates the three-tier workflow.

### Example Prompts

Below are example prompts you can use directly in OpenClaw to trigger the financial research skill:

---

#### 📈 Single-Stock Research
```
Research AAPL for me
```
```
Can you perform analysis for TSLA using the skill
```
```
Give me a full financial breakdown of GOOGL
```

#### 🏦 Sector-Specific Research
```
Research the top AI chip companies. Start with NVDA, then AMD.
```
```
Compare MSFT and AMZN for me using the financial research skill
```

#### 📁 Regulatory Deep-Dive
```
Download and summarize the latest 10-K filing for JPM
```
```
What are the key risk factors in Amazon's most recent annual report?
```

#### 🌐 Open Intelligence / Macro Research
```
What are the latest macroeconomic risks facing the Canadian banking sector?
```
```
Search for recent news on Federal Reserve interest rate decisions and their impact on tech stocks
```

#### 🇨🇦 Canadian Equities & ETFs (TSX)
```
Perform analysis for TSE:HHIC using the skill
```
```
Research RY.TO for me
```

#### 📊 Technical Analysis & Backtesting
```
Backtest the 20% flipper strategy on the S&P 500 universe
```
```
Check if the market regime is currently bullish or bearish
```
```
Run a Bollinger Band breakout strategy with $100k capital
```
```
Calculate performance metrics for my equity curve in equity.csv
```

---

## The Research Workflow (SKILL.md)

The skill follows three structured tiers, mirroring professional research platforms:

| Tier | Equivalent | Tool | Purpose |
|------|-----------|------|---------|
| 1 | Bloomberg | `stock_data.py` | Live market data, analyst ratings, news |
| 2 | FactSet / Refinitiv | `sec_edgar.py` | SEC 10-K / 10-Q filings & risk factors |
| 3 | Open APIs | `web_search.py` | Macro trends, competitor intelligence |

### Momentum Strategy Workflow (Trading Agent)

The trading agent follows a systematic five-phase workflow:

| Phase | Purpose | Script |
|-------|---------|--------|
| 1 | Data & Indicators | `fetch_market_data.py`, `calculate_indicators.py` |
| 2 | Market Filter | `check_index_filter.py` (Trend detection) |
| 3 | Signal Gen | `apply_100day_high_strategy.py`, `apply_bollinger_breakout.py`, etc. |
| 4 | Risk Mgmt | `manage_position_sizing.py`, `calculate_slippage_and_commissions.py` |
| 5 | Evaluation | `generate_performance_metrics.py`, `trading_agent_loop.py` |

Each research run or trading backtest concludes with detailed reports and performance metrics.

---

## Notes

- **SEC filings** are only available for US-listed companies registered with the SEC. For Canadian or international listings, the workflow automatically skips Tier 2 and relies more heavily on Tier 3 open web intelligence.
- **Yahoo Finance (yfinance)** rate limits may occasionally be encountered on Tier 1. Wait a few seconds and retry if this occurs.
- Results are saved as Markdown reports (e.g., `MSFT_Research_Report.md`) in the root directory for easy review.
