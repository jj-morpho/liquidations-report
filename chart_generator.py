"""
Chart generation module for Morpho risk reports.
Produces Morpho-branded matplotlib charts saved as PNG images.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from datetime import datetime
from config import COLORS, get_chain_color


# Global matplotlib style
plt.rcParams.update({
    "figure.facecolor": COLORS["bg_dark"],
    "axes.facecolor": COLORS["bg_card"],
    "axes.edgecolor": "#30363D",
    "axes.labelcolor": COLORS["text_light_gray"],
    "text.color": COLORS["text_white"],
    "xtick.color": COLORS["text_gray"],
    "ytick.color": COLORS["text_gray"],
    "grid.color": "#21262D",
    "grid.alpha": 0.6,
    "font.family": "sans-serif",
    "font.size": 11,
})


def format_usd(value, compact=True):
    """Format a USD value for display."""
    if value >= 1_000_000_000:
        return f"${value/1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value/1_000:.1f}K"
    else:
        return f"${value:,.0f}"


def usd_formatter(x, _):
    """Axis formatter for USD values."""
    if x >= 1_000_000:
        return f"${x/1_000_000:.1f}M"
    elif x >= 1_000:
        return f"${x/1_000:.0f}K"
    return f"${x:,.0f}"


def create_daily_liquidation_chart(daily_df, output_path="chart_daily_liquidations.png"):
    """
    Create a stacked bar chart of daily liquidations by chain over 7 days.
    Similar to the weekly liquidation amounts chart on data.morpho.org/risk.
    """
    if daily_df.empty:
        _create_no_data_chart("Daily Liquidations (7d)", output_path)
        return output_path

    # Pivot data: days as index, chains as columns
    daily_df = daily_df.copy()
    if "day" in daily_df.columns:
        daily_df["day"] = pd.to_datetime(daily_df["day"])
        daily_df["day_label"] = daily_df["day"].dt.strftime("%b %d")
    else:
        daily_df["day_label"] = [f"Day {i+1}" for i in range(len(daily_df))]

    pivot = daily_df.pivot_table(
        index="day_label", columns="blockchain",
        values="total_liquidated_usd", aggfunc="sum", fill_value=0
    )

    # Sort columns by total volume
    col_totals = pivot.sum().sort_values(ascending=False)
    pivot = pivot[col_totals.index]

    fig, ax = plt.subplots(figsize=(10, 5))

    # Stacked bar chart
    bottom = np.zeros(len(pivot))
    for chain in pivot.columns:
        color = get_chain_color(chain)
        bars = ax.bar(
            range(len(pivot)), pivot[chain].values,
            bottom=bottom, label=chain.capitalize(),
            color=color, width=0.6, edgecolor="none"
        )
        bottom += pivot[chain].values

    ax.set_xticks(range(len(pivot)))
    ax.set_xticklabels(pivot.index, rotation=0, fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(usd_formatter))
    ax.set_title("DAILY LIQUIDATION AMOUNTS (PAST 7 DAYS)", fontsize=13,
                 fontweight="bold", color=COLORS["text_white"], pad=15)
    ax.legend(loc="upper left", fontsize=8, framealpha=0.3,
              edgecolor="none", facecolor=COLORS["bg_card"])
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight",
                facecolor=COLORS["bg_dark"])
    plt.close(fig)
    return output_path


def create_liquidation_by_chain_chart(chain_df, output_path="chart_liq_by_chain.png"):
    """
    Create a horizontal bar chart showing liquidation volume per chain.
    """
    if chain_df.empty:
        _create_no_data_chart("Liquidations by Chain", output_path)
        return output_path

    chain_df = chain_df.copy().sort_values("total_liquidated_usd", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 4.5))

    chains = chain_df["blockchain"].str.capitalize()
    values = chain_df["total_liquidated_usd"]
    colors = [get_chain_color(c) for c in chain_df["blockchain"]]

    bars = ax.barh(chains, values, color=colors, height=0.55, edgecolor="none")

    # Add value labels
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + max(values) * 0.02, bar.get_y() + bar.get_height() / 2,
                format_usd(val), va="center", fontsize=9, color=COLORS["text_light_gray"])

    ax.xaxis.set_major_formatter(mticker.FuncFormatter(usd_formatter))
    ax.set_title("LIQUIDATION VOLUME BY CHAIN (PAST 7 DAYS)", fontsize=13,
                 fontweight="bold", color=COLORS["text_white"], pad=15)
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight",
                facecolor=COLORS["bg_dark"])
    plt.close(fig)
    return output_path


def create_bad_debt_summary_chart(bad_debt_df, unrealized_df, output_path="chart_bad_debt.png"):
    """
    Create a combined bad debt visualization showing realized vs unrealized.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4), gridspec_kw={"width_ratios": [1, 1.5]})

    # Left: Realized bad debt donut
    if bad_debt_df.empty or bad_debt_df.get("total_bad_debt_usd", pd.Series([0])).sum() == 0:
        ax1.text(0.5, 0.5, "$0", ha="center", va="center", fontsize=36,
                 fontweight="bold", color=COLORS["green"], transform=ax1.transAxes)
        ax1.text(0.5, 0.35, "Realized Bad Debt\n(Past 7 Days)", ha="center", va="center",
                 fontsize=10, color=COLORS["text_gray"], transform=ax1.transAxes)
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)
    else:
        chains = bad_debt_df["blockchain"].str.capitalize()
        values = bad_debt_df["total_bad_debt_usd"]
        colors = [get_chain_color(c) for c in bad_debt_df["blockchain"]]
        wedges, texts = ax1.pie(values, labels=chains, colors=colors,
                                startangle=90, textprops={"fontsize": 8})
        ax1.set_title("Realized Bad Debt by Chain", fontsize=10, color=COLORS["text_light_gray"])

    ax1.axis("off")

    # Right: Unrealized bad debt table (top markets)
    if not unrealized_df.empty and len(unrealized_df) > 0:
        # Take top 5
        top = unrealized_df.head(5).copy()
        table_data = []
        for _, row in top.iterrows():
            market = row.get("market", row.get("Market", "N/A"))
            chain = row.get("chain", row.get("Chain", "N/A"))
            debt = row.get("unrealized_bad_debt", row.get("Unrealized Bad Debt", 0))
            if isinstance(debt, str):
                debt = float(debt.replace("$", "").replace(",", ""))
            table_data.append([market[:25], chain, format_usd(debt)])

        ax2.axis("off")
        table = ax2.table(
            cellText=table_data,
            colLabels=["Market", "Chain", "Unrealized Debt"],
            loc="center",
            cellLoc="left",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1.0, 1.6)

        # Style the table
        for (row, col), cell in table.get_celld().items():
            cell.set_edgecolor("#30363D")
            if row == 0:
                cell.set_facecolor(COLORS["blue_primary"])
                cell.set_text_props(color="white", fontweight="bold")
            else:
                cell.set_facecolor(COLORS["bg_card"])
                cell.set_text_props(color=COLORS["text_light_gray"])

        ax2.set_title("TOP UNREALIZED BAD DEBT POSITIONS", fontsize=11,
                       fontweight="bold", color=COLORS["text_white"], pad=15)
    else:
        ax2.text(0.5, 0.5, "No unrealized bad debt", ha="center", va="center",
                 fontsize=14, color=COLORS["text_gray"], transform=ax2.transAxes)
        ax2.axis("off")

    fig.suptitle("BAD DEBT OVERVIEW", fontsize=13, fontweight="bold",
                 color=COLORS["text_white"], y=1.02)
    plt.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight",
                facecolor=COLORS["bg_dark"])
    plt.close(fig)
    return output_path


def create_kpi_card_image(metrics, output_path="chart_kpi_cards.png"):
    """
    Create a set of KPI cards similar to the top stats on data.morpho.org/risk.
    metrics: dict with keys like total_liquidated, positions, markets, chains, bad_debt
    """
    fig, axes = plt.subplots(1, 4, figsize=(10, 2.2))

    cards = [
        ("Total Liquidated", format_usd(metrics.get("total_liquidated_usd", 0)),
         COLORS["blue_primary"]),
        ("Positions Liquidated", f"{metrics.get('total_positions_liquidated', 0):,}",
         COLORS["blue_light"]),
        ("Markets Affected", f"{metrics.get('total_markets', 0)}",
         COLORS["cyan"]),
        ("Realized Bad Debt", format_usd(metrics.get("total_bad_debt_usd", 0)),
         COLORS["green"] if metrics.get("total_bad_debt_usd", 0) == 0 else COLORS["red"]),
    ]

    for ax, (label, value, color) in zip(axes, cards):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        # Card background
        rect = plt.Rectangle((0.05, 0.05), 0.9, 0.9, facecolor=COLORS["bg_card"],
                              edgecolor="#30363D", linewidth=1, transform=ax.transAxes,
                              clip_on=False, zorder=0)
        ax.add_patch(rect)
        # Value
        ax.text(0.5, 0.55, value, ha="center", va="center", fontsize=20,
                fontweight="bold", color=color, transform=ax.transAxes, zorder=1)
        # Label
        ax.text(0.5, 0.22, label, ha="center", va="center", fontsize=8,
                color=COLORS["text_gray"], transform=ax.transAxes, zorder=1)
        ax.axis("off")

    plt.tight_layout(pad=0.5)
    fig.savefig(output_path, dpi=200, bbox_inches="tight",
                facecolor=COLORS["bg_dark"])
    plt.close(fig)
    return output_path


def _create_no_data_chart(title, output_path):
    """Create a placeholder chart when no data is available."""
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.text(0.5, 0.5, "No data available for this period",
            ha="center", va="center", fontsize=16, color=COLORS["text_gray"],
            transform=ax.transAxes)
    ax.set_title(title, fontsize=13, fontweight="bold",
                 color=COLORS["text_white"], pad=15)
    ax.axis("off")
    fig.savefig(output_path, dpi=200, bbox_inches="tight",
                facecolor=COLORS["bg_dark"])
    plt.close(fig)


def generate_all_charts(report_data, output_dir="."):
    """Generate all charts from the fetched report data."""
    import os
    charts = {}

    # Extract summary metrics
    summary = report_data.get("weekly_summary", pd.DataFrame())
    if not summary.empty:
        metrics = summary.iloc[0].to_dict()
    else:
        metrics = {
            "total_liquidated_usd": 0,
            "total_bad_debt_usd": 0,
            "total_positions_liquidated": 0,
            "total_markets": 0,
            "total_chains": 0,
        }

    # 1. KPI Cards
    charts["kpi"] = create_kpi_card_image(
        metrics, os.path.join(output_dir, "chart_kpi_cards.png")
    )

    # 2. Daily liquidation chart
    charts["daily_liquidations"] = create_daily_liquidation_chart(
        report_data.get("daily_liquidations", pd.DataFrame()),
        os.path.join(output_dir, "chart_daily_liquidations.png")
    )

    # 3. Liquidation by chain
    charts["liq_by_chain"] = create_liquidation_by_chain_chart(
        report_data.get("liquidations_by_chain", pd.DataFrame()),
        os.path.join(output_dir, "chart_liq_by_chain.png")
    )

    # 4. Bad debt overview
    charts["bad_debt"] = create_bad_debt_summary_chart(
        report_data.get("bad_debt_by_chain", pd.DataFrame()),
        report_data.get("unrealized_bad_debt", pd.DataFrame()),
        os.path.join(output_dir, "chart_bad_debt.png")
    )

    return charts


if __name__ == "__main__":
    from data_fetcher import generate_sample_data
    data = generate_sample_data()
    charts = generate_all_charts(data, output_dir="/tmp")
    for name, path in charts.items():
        print(f"Generated: {name} -> {path}")
