"""
Chart generation module for Morpho risk reports.
Clean, plain style suitable for professional distribution.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from datetime import datetime
from config import COLORS, get_chain_color


# Plain white style
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#CCCCCC",
    "axes.labelcolor": "#333333",
    "text.color": "#222222",
    "xtick.color": "#555555",
    "ytick.color": "#555555",
    "grid.color": "#E0E0E0",
    "grid.alpha": 0.7,
    "font.family": "sans-serif",
    "font.size": 10,
})

# Muted color palette for charts
CHART_PALETTE = [
    "#4A7CBA",  # blue
    "#5DADE2",  # light blue
    "#7D3C98",  # purple
    "#E74C3C",  # red
    "#27AE60",  # green
    "#F39C12",  # orange
    "#1ABC9C",  # teal
    "#95A5A6",  # gray
]

def _get_chain_chart_color(chain, idx=0):
    """Get color for a chain, falling back to palette."""
    mapping = {
        "ethereum": "#4A7CBA",
        "base": "#2E86C1",
        "polygon": "#7D3C98",
        "optimism": "#E74C3C",
        "arbitrum": "#5DADE2",
        "hyperevm": "#1ABC9C",
        "unichain": "#C0392B",
        "katana": "#D4AC0D",
        "monad": "#AF7AC5",
    }
    return mapping.get(chain.lower(), CHART_PALETTE[idx % len(CHART_PALETTE)])


def format_usd(value, compact=True):
    if value >= 1_000_000_000:
        return f"${value/1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value/1_000:.1f}K"
    else:
        return f"${value:,.0f}"


def usd_formatter(x, _):
    if x >= 1_000_000:
        return f"${x/1_000_000:.1f}M"
    elif x >= 1_000:
        return f"${x/1_000:.0f}K"
    return f"${x:,.0f}"


def create_daily_liquidation_chart(daily_df, output_path="chart_daily_liquidations.png"):
    """Stacked bar chart of daily liquidations by chain over 7 days."""
    if daily_df.empty:
        _create_no_data_chart("Daily Liquidations (7d)", output_path)
        return output_path

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
    col_totals = pivot.sum().sort_values(ascending=False)
    pivot = pivot[col_totals.index]

    fig, ax = plt.subplots(figsize=(8, 3.8))

    bottom = np.zeros(len(pivot))
    for i, chain in enumerate(pivot.columns):
        color = _get_chain_chart_color(chain, i)
        ax.bar(range(len(pivot)), pivot[chain].values,
               bottom=bottom, label=chain.capitalize(),
               color=color, width=0.55, edgecolor="white", linewidth=0.5)
        bottom += pivot[chain].values

    ax.set_xticks(range(len(pivot)))
    ax.set_xticklabels(pivot.index, rotation=0, fontsize=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(usd_formatter))
    ax.set_title("Daily Liquidation Amounts (Past 7 Days)", fontsize=11, fontweight="bold", pad=10)
    ax.legend(loc="upper right", fontsize=7, frameon=True, edgecolor="#DDDDDD", fancybox=False)
    ax.grid(axis="y", linestyle="-", alpha=0.4)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


def create_liquidation_by_chain_chart(chain_df, output_path="chart_liq_by_chain.png"):
    """Horizontal bar chart of liquidation volume per chain."""
    if chain_df.empty:
        _create_no_data_chart("Liquidations by Chain", output_path)
        return output_path

    chain_df = chain_df.copy().sort_values("total_liquidated_usd", ascending=True)

    fig, ax = plt.subplots(figsize=(8, 3.5))

    chains = chain_df["blockchain"].str.capitalize()
    values = chain_df["total_liquidated_usd"]
    colors = [_get_chain_chart_color(c, i) for i, c in enumerate(chain_df["blockchain"])]

    bars = ax.barh(chains, values, color=colors, height=0.5, edgecolor="white", linewidth=0.5)

    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + max(values) * 0.02, bar.get_y() + bar.get_height() / 2,
                format_usd(val), va="center", fontsize=8, color="#555555")

    ax.xaxis.set_major_formatter(mticker.FuncFormatter(usd_formatter))
    ax.set_title("Liquidation Volume by Chain (Past 7 Days)", fontsize=11, fontweight="bold", pad=10)
    ax.grid(axis="x", linestyle="-", alpha=0.4)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


def create_bad_debt_summary_chart(bad_debt_df, unrealized_df, output_path="chart_bad_debt.png"):
    """Bad debt visualization — realized vs unrealized."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.2), gridspec_kw={"width_ratios": [1, 1.5]})

    # Left: realized
    if bad_debt_df.empty or bad_debt_df.get("total_bad_debt_usd", pd.Series([0])).sum() == 0:
        ax1.text(0.5, 0.55, "$0", ha="center", va="center", fontsize=32,
                 fontweight="bold", color="#27AE60", transform=ax1.transAxes)
        ax1.text(0.5, 0.35, "Realized Bad Debt\n(Past 7 Days)", ha="center", va="center",
                 fontsize=9, color="#888888", transform=ax1.transAxes)
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)
    else:
        chains = bad_debt_df["blockchain"].str.capitalize()
        values = bad_debt_df["total_bad_debt_usd"]
        colors = [_get_chain_chart_color(c, i) for i, c in enumerate(bad_debt_df["blockchain"])]
        ax1.pie(values, labels=chains, colors=colors, startangle=90, textprops={"fontsize": 8})
        ax1.set_title("Realized Bad Debt by Chain", fontsize=9, color="#555555")
    ax1.axis("off")

    # Right: unrealized table
    if not unrealized_df.empty and len(unrealized_df) > 0:
        top = unrealized_df.head(5).copy()
        table_data = []
        for _, row in top.iterrows():
            market = row.get("market", row.get("Market", "N/A"))
            chain = row.get("chain", row.get("Chain", "N/A"))
            debt = row.get("unrealized_bad_debt", row.get("Unrealized Bad Debt", 0))
            if isinstance(debt, str):
                debt = float(debt.replace("$", "").replace(",", ""))
            table_data.append([market[:28], chain, format_usd(debt)])

        ax2.axis("off")
        table = ax2.table(
            cellText=table_data,
            colLabels=["Market", "Chain", "Unrealized Debt"],
            loc="center", cellLoc="left",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(7.5)
        table.scale(1.0, 1.5)

        for (row, col), cell in table.get_celld().items():
            cell.set_edgecolor("#DDDDDD")
            if row == 0:
                cell.set_facecolor("#4A7CBA")
                cell.set_text_props(color="white", fontweight="bold")
            else:
                cell.set_facecolor("#F8F9FA" if row % 2 == 0 else "white")
                cell.set_text_props(color="#333333")

        ax2.set_title("Top Unrealized Bad Debt Positions", fontsize=10, fontweight="bold", pad=12)
    else:
        ax2.text(0.5, 0.5, "No unrealized bad debt", ha="center", va="center",
                 fontsize=12, color="#999999", transform=ax2.transAxes)
        ax2.axis("off")

    plt.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


def create_vault_liquidity_chart(vault_name, vault_df, output_path="chart_vault_liq.png"):
    """Area chart showing vault liquidity % and total assets over time (like Dune query 6376752)."""
    if vault_df.empty:
        _create_no_data_chart(f"{vault_name} - Liquidity", output_path)
        return output_path

    df = vault_df.copy()
    df["hour"] = pd.to_datetime(df["hour"])
    df = df.sort_values("hour")
    df["liquidity_pct"] = (df["liquidity_usd"] / df["total_assets_usd"].replace(0, 1)) * 100

    fig, ax1 = plt.subplots(figsize=(7, 2.8))

    # Left y-axis: Liquidity %
    ax1.fill_between(df["hour"], df["liquidity_pct"], alpha=0.25, color="#4A7CBA")
    ax1.plot(df["hour"], df["liquidity_pct"], color="#4A7CBA", linewidth=1.2, label="Liquidity %")
    ax1.set_ylabel("Liquidity %", fontsize=8, color="#4A7CBA")
    ax1.tick_params(axis="y", labelcolor="#4A7CBA", labelsize=7)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax1.set_ylim(bottom=0)

    # Right y-axis: Total Assets
    ax2 = ax1.twinx()
    ax2.plot(df["hour"], df["total_assets_usd"], color="#E67E22", linewidth=1.0,
             alpha=0.7, linestyle="--", label="Total Assets")
    ax2.set_ylabel("Total Assets", fontsize=8, color="#E67E22")
    ax2.tick_params(axis="y", labelcolor="#E67E22", labelsize=7)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(usd_formatter))

    # X-axis
    ax1.tick_params(axis="x", labelsize=7)
    fig.autofmt_xdate(rotation=0)
    import matplotlib.dates as mdates
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=2))

    # Title
    avg_liq = df["liquidity_pct"].mean()
    latest_assets = df["total_assets_usd"].iloc[-1]
    ax1.set_title(
        f"{vault_name}  |  Avg Liquidity: {avg_liq:.1f}%  |  Assets: {format_usd(latest_assets)}",
        fontsize=9, fontweight="bold", pad=8
    )

    ax1.grid(axis="y", linestyle="-", alpha=0.3)
    ax1.set_axisbelow(True)
    ax1.spines["top"].set_visible(False)
    ax2.spines["top"].set_visible(False)

    plt.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


def create_kpi_card_image(metrics, output_path="chart_kpi_cards.png"):
    """KPI summary cards — not used in plain mode (handled as text in PDF)."""
    # We skip this for the plain format — the PDF will render KPIs as text
    fig, ax = plt.subplots(figsize=(1, 1))
    ax.axis("off")
    fig.savefig(output_path, dpi=50, facecolor="white")
    plt.close(fig)
    return output_path


def _create_no_data_chart(title, output_path):
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.text(0.5, 0.5, "No data available for this period",
            ha="center", va="center", fontsize=13, color="#999999", transform=ax.transAxes)
    ax.set_title(title, fontsize=11, fontweight="bold", pad=10)
    ax.axis("off")
    fig.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def generate_all_charts(report_data, output_dir="."):
    """Generate all charts from the fetched report data."""
    import os
    charts = {}

    summary = report_data.get("weekly_summary", pd.DataFrame())
    if not summary.empty:
        metrics = summary.iloc[0].to_dict()
    else:
        metrics = {"total_liquidated_usd": 0, "total_bad_debt_usd": 0,
                   "total_positions_liquidated": 0, "total_markets": 0, "total_chains": 0}

    charts["kpi"] = create_kpi_card_image(metrics, os.path.join(output_dir, "chart_kpi_cards.png"))
    charts["daily_liquidations"] = create_daily_liquidation_chart(
        report_data.get("daily_liquidations", pd.DataFrame()),
        os.path.join(output_dir, "chart_daily_liquidations.png"))
    charts["liq_by_chain"] = create_liquidation_by_chain_chart(
        report_data.get("liquidations_by_chain", pd.DataFrame()),
        os.path.join(output_dir, "chart_liq_by_chain.png"))
    charts["bad_debt"] = create_bad_debt_summary_chart(
        report_data.get("bad_debt_by_chain", pd.DataFrame()),
        report_data.get("unrealized_bad_debt", pd.DataFrame()),
        os.path.join(output_dir, "chart_bad_debt.png"))

    # Vault liquidity charts
    vault_liquidity = report_data.get("vault_liquidity", {})
    charts["vault_charts"] = {}
    for vault_name, vault_df in vault_liquidity.items():
        safe_name = vault_name.lower().replace(" ", "_").replace("/", "_")
        path = os.path.join(output_dir, f"chart_vault_{safe_name}.png")
        charts["vault_charts"][vault_name] = create_vault_liquidity_chart(
            vault_name, vault_df, path
        )

    return charts
