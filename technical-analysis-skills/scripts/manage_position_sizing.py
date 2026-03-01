#!/usr/bin/env python3
"""Equal-slot position sizing for portfolio-level risk management."""

import sys
import click
import pandas as pd
import math


def allocate_positions(signals_df, total_capital, num_slots):
    """Allocate capital across BUY signals using equal-slot sizing.

    Args:
        signals_df: DataFrame with columns 'Ticker', 'Close', 'Signal'.
                    Only rows with Signal == 'BUY' are considered.
        total_capital: Total portfolio capital in dollars.
        num_slots: Number of equal-weight position slots.

    Returns:
        DataFrame with columns: Ticker, Close, Capital_Per_Slot, Shares, Allocated.
    """
    capital_per_slot = total_capital / num_slots
    buys = signals_df[signals_df["Signal"] == "BUY"].copy()

    if buys.empty:
        return pd.DataFrame(columns=["Ticker", "Close", "Capital_Per_Slot", "Shares", "Allocated"])

    # Take unique tickers — if multiple BUY rows exist, use the latest (last) one
    buys = buys.groupby("Ticker").tail(1).copy()

    # Limit to available slots
    if len(buys) > num_slots:
        click.secho(
            f"Warning: {len(buys)} signals exceed {num_slots} slots. "
            f"Taking the first {num_slots} by date order.",
            fg="yellow", err=True,
        )
        buys = buys.head(num_slots)

    buys["Capital_Per_Slot"] = capital_per_slot
    buys["Shares"] = buys.apply(
        lambda row: math.floor(capital_per_slot / row["Close"]) if row["Close"] > 0 else 0,
        axis=1,
    )
    buys["Allocated"] = buys["Shares"] * buys["Close"]

    return buys[["Ticker", "Close", "Capital_Per_Slot", "Shares", "Allocated"]].reset_index(drop=True)


@click.command()
@click.option("--capital", default=100000.0, type=float, help="Total portfolio capital (default 100000).")
@click.option("--slots", default=20, type=int, help="Number of equal position slots (default 20).")
@click.option("--signals", required=True, type=click.Path(exists=True),
              help="CSV file with Ticker, Close, Signal columns.")
@click.option("--output", default=None, help="Save allocations to this CSV path.")
def main(capital, slots, signals, output):
    """Divide CAPITAL into SLOTS equal positions based on BUY signals in SIGNALS CSV.

    Each position gets capital / slots dollars. Shares are rounded down to
    whole numbers. If more BUY signals exist than slots, the earliest by
    date are prioritized.
    """
    df = pd.read_csv(signals, parse_dates=["Date"] if "Date" in pd.read_csv(signals, nrows=0).columns else [])

    if "Ticker" not in df.columns or "Close" not in df.columns or "Signal" not in df.columns:
        click.secho("Error: signals CSV must have Ticker, Close, and Signal columns.", fg="red")
        sys.exit(1)

    alloc = allocate_positions(df, capital, slots)

    if alloc.empty:
        click.secho("No BUY signals to allocate.", fg="yellow")
        return

    if output:
        alloc.to_csv(output, index=False)
        click.secho(f"Saved {len(alloc)} allocations to {output}", fg="green")
    else:
        click.echo(alloc.to_string(index=False))

    total_allocated = alloc["Allocated"].sum()
    remaining = capital - total_allocated
    click.secho(f"\n--- Position Sizing Summary ---", fg="cyan", bold=True)
    click.echo(f"  Capital:    ${capital:,.2f}")
    click.echo(f"  Slots:      {slots}")
    click.echo(f"  Per slot:   ${capital / slots:,.2f}")
    click.echo(f"  Positions:  {len(alloc)}")
    click.echo(f"  Allocated:  ${total_allocated:,.2f}")
    click.echo(f"  Remaining:  ${remaining:,.2f}")


if __name__ == "__main__":
    main()
