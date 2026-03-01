#!/usr/bin/env python3
"""Automated tests for technical analysis indicator and strategy functions."""

import sys
import os
import math
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from calculate_indicators import add_sma, add_bollinger_bands, add_donchian_channels
from check_index_filter import get_index_regime
from apply_20percent_flipper import signal_20pct_flipper
from apply_100day_high_strategy import signal_100day_high
from apply_bollinger_breakout import signal_bollinger_breakout
from manage_position_sizing import allocate_positions
from calculate_slippage_and_commissions import apply_costs
from generate_performance_metrics import compute_metrics


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_df():
    """10-row DataFrame with known values for easy hand-verification."""
    prices = [10, 11, 12, 11, 13, 14, 12, 15, 14, 16]
    dates = pd.date_range("2024-01-01", periods=10, freq="B")
    return pd.DataFrame({
        "Open": prices,
        "High": [p + 1 for p in prices],
        "Low": [p - 1 for p in prices],
        "Close": prices,
        "Volume": [1000] * 10,
    }, index=dates)


@pytest.fixture
def long_df():
    """200-row DataFrame with a simple upward trend for indicator tests."""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=200, freq="B")
    base = np.linspace(100, 200, 200) + np.random.normal(0, 3, 200)
    return pd.DataFrame({
        "Open": base - 0.5,
        "High": base + 2,
        "Low": base - 2,
        "Close": base,
        "Volume": np.random.randint(1000, 10000, 200),
    }, index=dates)


# ---------------------------------------------------------------------------
# SMA Tests
# ---------------------------------------------------------------------------

class TestSMA:
    def test_sma_5_on_simple_data(self, simple_df):
        """Verify SMA_5 matches hand-calculated rolling mean."""
        df = add_sma(simple_df, periods=[5])
        # First 4 rows should be NaN (need 5 points)
        assert df["SMA_5"].isna().sum() == 4
        # Row index 4 (5th row): mean of [10,11,12,11,13] = 57/5 = 11.4
        assert round(df["SMA_5"].iloc[4], 1) == 11.4
        # Row index 5: mean of [11,12,11,13,14] = 61/5 = 12.2
        assert round(df["SMA_5"].iloc[5], 1) == 12.2

    def test_sma_default_periods(self, long_df):
        """Default SMA periods (50, 75, 200) should produce correct columns."""
        df = add_sma(long_df)
        assert "SMA_50" in df.columns
        assert "SMA_75" in df.columns
        assert "SMA_200" in df.columns
        # SMA_50 should have 49 NaN rows
        assert df["SMA_50"].isna().sum() == 49

    def test_sma_values_are_averages(self, long_df):
        """SMA at any point should equal the mean of the preceding N closes."""
        df = add_sma(long_df, periods=[50])
        idx = 100
        expected = df["Close"].iloc[idx - 49:idx + 1].mean()
        assert abs(df["SMA_50"].iloc[idx] - expected) < 1e-10


# ---------------------------------------------------------------------------
# Bollinger Band Tests
# ---------------------------------------------------------------------------

class TestBollingerBands:
    def test_bands_are_symmetric(self, long_df):
        """Upper and lower bands should be equidistant from mid."""
        df = add_bollinger_bands(long_df, period=50, num_std=2)
        valid = df.dropna(subset=["BB_Mid"])
        upper_dist = valid["BB_Upper"] - valid["BB_Mid"]
        lower_dist = valid["BB_Mid"] - valid["BB_Lower"]
        np.testing.assert_array_almost_equal(upper_dist.values, lower_dist.values)

    def test_bands_match_manual_calc(self, long_df):
        """Verify bands at a specific index match hand-calculated ±2σ."""
        period = 50
        df = add_bollinger_bands(long_df, period=period, num_std=2)
        idx = 100
        window = df["Close"].iloc[idx - period + 1:idx + 1]
        expected_mid = window.mean()
        expected_std = window.std()
        assert abs(df["BB_Mid"].iloc[idx] - expected_mid) < 1e-10
        assert abs(df["BB_Upper"].iloc[idx] - (expected_mid + 2 * expected_std)) < 1e-10
        assert abs(df["BB_Lower"].iloc[idx] - (expected_mid - 2 * expected_std)) < 1e-10


# ---------------------------------------------------------------------------
# Donchian Channel Tests
# ---------------------------------------------------------------------------

class TestDonchianChannels:
    def test_dc_high_is_rolling_max(self, long_df):
        """DC_High should be the rolling max of the High column."""
        period = 20
        df = add_donchian_channels(long_df, period=period)
        idx = 50
        expected = df["High"].iloc[idx - period + 1:idx + 1].max()
        assert abs(df["DC_High"].iloc[idx] - expected) < 1e-10

    def test_dc_low_is_rolling_min(self, long_df):
        """DC_Low should be the rolling min of the Low column."""
        period = 20
        df = add_donchian_channels(long_df, period=period)
        idx = 50
        expected = df["Low"].iloc[idx - period + 1:idx + 1].min()
        assert abs(df["DC_Low"].iloc[idx] - expected) < 1e-10

    def test_dc_nan_count(self, long_df):
        """First (period - 1) rows should be NaN."""
        period = 100
        df = add_donchian_channels(long_df, period=period)
        assert df["DC_High"].isna().sum() == period - 1


# ---------------------------------------------------------------------------
# Trailing Stop (20% Flipper) Tests
# ---------------------------------------------------------------------------

class TestTrailingStop:
    def test_sell_on_20pct_drop(self):
        """A 20% drop from peak should trigger a SELL signal."""
        # Build a price series: rise to 100, then drop 25% to 75
        prices = list(range(50, 101)) + [90, 85, 80, 75]
        dates = pd.date_range("2023-01-01", periods=len(prices), freq="B")
        df = pd.DataFrame({
            "Open": prices,
            "High": [p + 0.5 for p in prices],
            "Low": [p - 0.5 for p in prices],
            "Close": prices,
            "Volume": [1000] * len(prices),
        }, index=dates)

        # Use a short entry period so we get a BUY early
        result = signal_20pct_flipper(df, stop_pct=20.0, entry_period=10)
        signals = result["Signal"].tolist()
        assert "BUY" in signals
        assert "SELL" in signals
        # The SELL should come after the price drops to 80 (20% below peak of 100)
        sell_rows = result[result["Signal"] == "SELL"]
        assert not sell_rows.empty
        assert sell_rows.iloc[0]["Close"] <= 80  # 80 = 100 * 0.80

    def test_no_sell_without_sufficient_drop(self):
        """If price stays within 20% of peak, no SELL should fire."""
        prices = list(range(50, 101)) + [95, 92, 90, 88, 85]
        dates = pd.date_range("2023-01-01", periods=len(prices), freq="B")
        df = pd.DataFrame({
            "Open": prices,
            "High": [p + 0.5 for p in prices],
            "Low": [p - 0.5 for p in prices],
            "Close": prices,
            "Volume": [1000] * len(prices),
        }, index=dates)
        result = signal_20pct_flipper(df, stop_pct=20.0, entry_period=10)
        # 85 = 15% drop from 100 — should NOT trigger SELL yet
        assert "SELL" not in result["Signal"].tolist()


# ---------------------------------------------------------------------------
# Position Sizing Tests
# ---------------------------------------------------------------------------

class TestPositionSizing:
    def test_equal_allocation(self):
        """Each slot should get capital / slots dollars."""
        df = pd.DataFrame({
            "Ticker": ["AAPL", "MSFT"],
            "Close": [150.0, 300.0],
            "Signal": ["BUY", "BUY"],
        })
        alloc = allocate_positions(df, total_capital=100000, num_slots=10)
        assert len(alloc) == 2
        assert all(alloc["Capital_Per_Slot"] == 10000.0)
        # Shares should be floor(10000 / price)
        assert alloc.iloc[0]["Shares"] == math.floor(10000 / 150)
        assert alloc.iloc[1]["Shares"] == math.floor(10000 / 300)

    def test_excess_signals_capped(self):
        """More BUY signals than slots should be capped."""
        df = pd.DataFrame({
            "Ticker": [f"T{i}" for i in range(5)],
            "Close": [100.0] * 5,
            "Signal": ["BUY"] * 5,
        })
        alloc = allocate_positions(df, total_capital=10000, num_slots=3)
        assert len(alloc) == 3


# ---------------------------------------------------------------------------
# Cost Modeling Tests
# ---------------------------------------------------------------------------

class TestCostModeling:
    def test_commission_applied(self):
        """Commission should be at least the minimum flat fee."""
        df = pd.DataFrame({
            "Close": [10.0],
            "Shares": [5],
            "Signal": ["BUY"],
        })
        result = apply_costs(df, commission_pct=0.25, min_commission=10.0, slippage_pct=0)
        # Gross = 10 * 5 = 50; 0.25% of 50 = 0.125 < min 10 → commission = 10
        assert result["Commission"].iloc[0] == 10.0

    def test_slippage_direction(self):
        """Buys should pay more; sells should receive less."""
        df = pd.DataFrame({
            "Close": [100.0, 100.0],
            "Shares": [10, 10],
            "Signal": ["BUY", "SELL"],
        })
        result = apply_costs(df, commission_pct=0, min_commission=0, slippage_pct=1.0)
        assert result.iloc[0]["Slippage_Adj_Price"] > 100.0  # buy pays more
        assert result.iloc[1]["Slippage_Adj_Price"] < 100.0  # sell receives less


# ---------------------------------------------------------------------------
# Performance Metrics Tests
# ---------------------------------------------------------------------------

class TestPerformanceMetrics:
    def test_cagr_and_drawdown(self):
        """CAGR and drawdown should be computed correctly for a known curve."""
        dates = pd.date_range("2020-01-01", periods=365 * 2, freq="D")
        # Steady growth from 100 to 200 over 2 years
        equity = pd.Series(np.linspace(100, 200, len(dates)), index=dates)
        metrics = compute_metrics(equity)
        # CAGR should be ~41.4% (sqrt(2) - 1)
        assert 40 < metrics["cagr"] < 43
        # No drawdown in a monotonically increasing series
        assert metrics["max_drawdown"] == 0.0 or abs(metrics["max_drawdown"]) < 0.01

    def test_drawdown_with_dip(self):
        """A known dip should produce the correct max drawdown."""
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        prices = [100] * 50 + [80] * 10 + [100] * 40  # 20% dip mid-series
        equity = pd.Series(prices, index=dates, dtype=float)
        metrics = compute_metrics(equity)
        assert abs(metrics["max_drawdown"] - (-20.0)) < 0.1  # -20%


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
