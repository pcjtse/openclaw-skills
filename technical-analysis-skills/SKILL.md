---
name: Technical Analysis Trading Agent
description: A modular momentum-based trading agent inspired by Nick Radge's "Unholy Grails". Use when the user wants to (1) backtest momentum or breakout strategies on equities, (2) check market regime filters for bull/bear conditions, (3) generate entry/exit signals using Donchian, Bollinger, or trailing-stop methods, (4) evaluate strategy performance with MAR ratio and underwater equity curves. Covers data fetching, indicator calculation, market regime detection, position sizing, cost modeling, and full orchestration.
---

# Technical Analysis Trading Agent Skill

A modular trading agent based on momentum strategies and risk management principles from *Unholy Grails* by Nick Radge. The system prioritizes capital preservation and statistical expectancy.

## When to Use

Trigger this skill when:
- User wants to backtest a momentum or breakout strategy
- User asks about market regime detection (bull/bear filter)
- User wants to screen stocks for technical breakout signals
- User needs portfolio-level position sizing or cost modeling
- User asks for strategy performance metrics (CAGR, drawdown, MAR ratio)

## Prerequisites

Install the required dependencies:
```bash
pip install -r scripts/requirements.txt
```

## Workflow

The trading agent follows a systematic five-phase workflow. Each phase has its own script that can be used independently or chained together via the orchestration loop.

### Phase 1: Fetch Data & Calculate Indicators

```bash
# Fetch OHLCV data for one or more tickers
python scripts/fetch_market_data.py SPY,AAPL,MSFT --start 2023-01-01 --output universe_data.csv

# Calculate technical indicators (SMA, Bollinger Bands, Donchian Channels)
python scripts/calculate_indicators.py universe_data.csv --output universe_indicators.csv
```

### Phase 2: Check Market Regime

```bash
# Determine if the broad market is bullish or bearish
python scripts/check_index_filter.py --index ^GSPC --period 75
```

If the regime is **BEARISH**, the agent should halt new entries and consider defensive exits.

### Phase 3: Generate Strategy Signals

Choose one of three momentum strategies:

```bash
# 100-day high breakout (Donchian)
python scripts/apply_100day_high_strategy.py universe_indicators.csv

# Bollinger Band breakout
python scripts/apply_bollinger_breakout.py universe_indicators.csv

# 20% trailing-stop flipper
python scripts/apply_20percent_flipper.py universe_indicators.csv --stop-pct 20
```

### Phase 4: Position Sizing & Cost Modeling

```bash
# Allocate capital across positions using equal-slot sizing
python scripts/manage_position_sizing.py --capital 100000 --slots 20 --signals signals.csv

# Apply realistic commissions and slippage
python scripts/calculate_slippage_and_commissions.py --trades trades.csv --commission-pct 0.25 --slippage-pct 0.1
```

### Phase 5: Evaluate & Orchestrate

```bash
# Generate performance metrics and underwater equity curve
python scripts/generate_performance_metrics.py --equity-csv equity.csv

# Run the full orchestration loop end-to-end
python scripts/trading_agent_loop.py --universe universe.csv --capital 100000 --strategy bollinger
```

## Output

The trading agent produces:
1. **Signal reports** — CSV with BUY/SELL/HOLD signals per ticker per date
2. **Position allocations** — CSV with ticker, shares, and capital allocated
3. **Performance metrics** — JSON with CAGR, Max Drawdown, and MAR Ratio
4. **Underwater equity curve** — CSV showing drawdown-from-peak over time
