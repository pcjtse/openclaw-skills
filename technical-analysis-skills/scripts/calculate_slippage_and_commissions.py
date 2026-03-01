#!/usr/bin/env python3
"""Apply realistic commissions and slippage to trade records."""

import sys
import click
import pandas as pd


def apply_costs(trades_df, commission_pct=0.25, min_commission=10.0, slippage_pct=0.10):
    """Adjust trade prices for commissions and slippage.

    For BUY trades, slippage increases the effective price; for SELL trades,
    slippage decreases it (worst-case assumption).

    Args:
        trades_df: DataFrame with columns 'Close', 'Shares', 'Signal'.
        commission_pct: Commission as a percentage of trade value (default 0.25%).
        min_commission: Minimum commission fee in dollars (default $10).
        slippage_pct: Estimated slippage as a percentage (default 0.10%).

    Returns:
        DataFrame with added columns: Slippage_Adj_Price, Gross_Value,
        Commission, Net_Cost (for buys) or Net_Proceeds (for sells).
    """
    df = trades_df.copy()
    slip_frac = slippage_pct / 100.0
    comm_frac = commission_pct / 100.0

    # Determine direction multiplier: buys pay more, sells receive less
    is_buy = df["Signal"].str.upper() == "BUY"
    df["Slippage_Adj_Price"] = df["Close"] * (1 + slip_frac)         # buys default
    df.loc[~is_buy, "Slippage_Adj_Price"] = df.loc[~is_buy, "Close"] * (1 - slip_frac)

    df["Gross_Value"] = df["Slippage_Adj_Price"] * df["Shares"]

    df["Commission"] = (df["Gross_Value"] * comm_frac).clip(lower=min_commission)

    # Net cost for buys (you pay more), net proceeds for sells (you receive less)
    df["Net_Value"] = df["Gross_Value"] + df["Commission"]           # buys
    df.loc[~is_buy, "Net_Value"] = df.loc[~is_buy, "Gross_Value"] - df.loc[~is_buy, "Commission"]

    return df


@click.command()
@click.option("--trades", required=True, type=click.Path(exists=True),
              help="CSV file with trade records (needs Close, Shares, Signal columns).")
@click.option("--commission-pct", default=0.25, type=float,
              help="Commission percentage (default 0.25%).")
@click.option("--min-commission", default=10.0, type=float,
              help="Minimum flat commission fee in dollars (default $10).")
@click.option("--slippage-pct", default=0.10, type=float,
              help="Slippage percentage (default 0.10%).")
@click.option("--output", default=None, help="Save adjusted trades to this CSV path.")
def main(trades, commission_pct, min_commission, slippage_pct, output):
    """Apply commissions and slippage to trade records in TRADES CSV.

    Produces adjusted trade values with realistic cost assumptions for
    backtesting accuracy.
    """
    df = pd.read_csv(trades)
    required = {"Close", "Shares", "Signal"}
    missing = required - set(df.columns)
    if missing:
        click.secho(f"Error: trades CSV missing columns: {', '.join(missing)}", fg="red")
        sys.exit(1)

    result = apply_costs(df, commission_pct, min_commission, slippage_pct)

    if output:
        result.to_csv(output, index=False)
        click.secho(f"Saved adjusted trades to {output}", fg="green")
    else:
        cols = ["Close", "Slippage_Adj_Price", "Shares", "Gross_Value", "Commission", "Net_Value", "Signal"]
        display_cols = [c for c in cols if c in result.columns]
        click.echo(result[display_cols].to_string(index=False))

    total_comm = result["Commission"].sum()
    total_slip = (result["Slippage_Adj_Price"] - result["Close"]).abs().sum() * result["Shares"].mean()
    click.secho(f"\n--- Cost Summary ---", fg="cyan", bold=True)
    click.echo(f"  Commission rate: {commission_pct}% (min ${min_commission:.2f})")
    click.echo(f"  Slippage rate:   {slippage_pct}%")
    click.echo(f"  Total commissions: ${total_comm:,.2f}")
    click.echo(f"  Trades processed:  {len(result)}")


if __name__ == "__main__":
    main()
