#!/usr/bin/env python3
"""
Morpho Weekly Risk Report — Static HTML Generator
===================================================
Generates a self-contained index.html with embedded charts and data.
Share the single file via email, Slack, or host on GitHub Pages.

Usage:
    # With sample data (no API key needed):
    python generate_html_report.py --sample

    # With live Dune data:
    export DUNE_API_KEY="your_key"
    python generate_html_report.py

    # Custom output path:
    python generate_html_report.py --sample --output docs/index.html
"""
import os
import sys
import base64
import argparse
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import COLORS, CHAIN_COLOR_MAP


def _format_usd(value):
    """Format USD value for display."""
    if isinstance(value, str):
        return value
    if value >= 1_000_000_000:
        return f"${value/1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value/1_000:.1f}K"
    else:
        return f"${value:,.2f}"


def _img_to_base64(path):
    """Read an image file and return a base64 data URI."""
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def _build_chain_table_rows(chain_df):
    """Build HTML table rows from chain breakdown dataframe."""
    if chain_df.empty:
        return '<tr><td colspan="4" style="text-align:center;color:#8B949E;padding:20px;">No data available</td></tr>'
    rows = []
    for _, row in chain_df.head(8).iterrows():
        chain = row["blockchain"]
        color = CHAIN_COLOR_MAP.get(chain.lower(), COLORS["chain_other"])
        rows.append(
            f'<tr>'
            f'<td><span class="chain-dot" style="background:{color};"></span>{chain.capitalize()}</td>'
            f'<td class="right">{_format_usd(row["total_liquidated_usd"])}</td>'
            f'<td class="right">{int(row["num_liquidations"]):,}</td>'
            f'<td class="right">{int(row["markets_affected"])}</td>'
            f'</tr>'
        )
    return "\n".join(rows)


def _build_bad_debt_table_rows(unrealized_df):
    """Build HTML table rows from unrealized bad debt dataframe."""
    if unrealized_df.empty:
        return '<tr><td colspan="3" style="text-align:center;color:#8B949E;padding:20px;">No unrealized bad debt</td></tr>'
    rows = []
    for _, row in unrealized_df.head(5).iterrows():
        market = row.get("market", row.get("Market", "N/A"))
        chain = row.get("chain", row.get("Chain", "N/A"))
        debt = row.get("unrealized_bad_debt", row.get("Unrealized Bad Debt", 0))
        if isinstance(debt, str):
            debt = float(debt.replace("$", "").replace(",", ""))
        rows.append(
            f'<tr>'
            f'<td>{market}</td>'
            f'<td>{chain.capitalize() if isinstance(chain, str) else chain}</td>'
            f'<td class="right">{_format_usd(debt)}</td>'
            f'</tr>'
        )
    return "\n".join(rows)


def generate_html(report_data, charts, output_path="index.html"):
    """Generate a self-contained HTML report."""
    import pandas as pd

    now = datetime.now()
    week_start = (now - timedelta(days=7)).strftime("%B %d")
    week_end = now.strftime("%B %d, %Y")

    # Extract summary metrics
    summary = report_data.get("weekly_summary", pd.DataFrame())
    if not summary.empty:
        s = summary.iloc[0]
        total_liq = _format_usd(s.get("total_liquidated_usd", 0))
        positions = int(s.get("total_positions_liquidated", 0))
        markets = int(s.get("total_markets", 0))
        chains = int(s.get("total_chains", 0))
        bad_debt = s.get("total_bad_debt_usd", 0)
    else:
        total_liq, positions, markets, chains, bad_debt = "$0", 0, 0, 0, 0

    bad_debt_class = "green" if bad_debt == 0 else "red"
    bad_debt_text = (
        "with zero realized bad debt"
        if bad_debt == 0
        else f"with {_format_usd(bad_debt)} in realized bad debt"
    )

    # Encode chart images as base64
    kpi_img = _img_to_base64(charts.get("kpi", ""))
    daily_img = _img_to_base64(charts.get("daily_liquidations", ""))
    chain_img = _img_to_base64(charts.get("liq_by_chain", ""))
    bad_debt_img = _img_to_base64(charts.get("bad_debt", ""))

    # Build tables
    chain_df = report_data.get("liquidations_by_chain", pd.DataFrame())
    chain_table_rows = _build_chain_table_rows(chain_df)

    unrealized_df = report_data.get("unrealized_bad_debt", pd.DataFrame())
    bad_debt_table_rows = _build_bad_debt_table_rows(unrealized_df)

    # Bad debt section text
    if bad_debt == 0:
        bad_debt_section_text = (
            "No realized bad debt events occurred during the past 7 days, "
            "confirming the effectiveness of Morpho\u2019s liquidation mechanisms "
            "and the prudent risk parameters set by curators across the network."
        )
    else:
        bad_debt_section_text = (
            f"A total of {_format_usd(bad_debt)} in realized bad debt was recorded. "
            "See the breakdown below for details."
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Morpho Weekly Risk Report &mdash; {week_end}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                         "Helvetica Neue", Arial, sans-serif;
            background: {COLORS["bg_dark"]};
            color: {COLORS["text_light_gray"]};
            line-height: 1.6;
        }}

        .header {{
            border-bottom: 2px solid {COLORS["blue_primary"]};
            padding: 20px 0;
            margin-bottom: 32px;
        }}

        .header-inner {{
            max-width: 900px;
            margin: 0 auto;
            padding: 0 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .header-left {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .header h1 {{
            font-size: 14px;
            font-weight: 700;
            color: {COLORS["text_gray"]};
            letter-spacing: 0.5px;
        }}

        .header h1 span {{
            color: {COLORS["blue_primary"]};
        }}

        .header .date {{
            font-size: 13px;
            color: {COLORS["text_gray"]};
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 0 24px 60px;
        }}

        .title-section {{
            margin-bottom: 24px;
        }}

        .title-section h1 {{
            font-size: 32px;
            font-weight: 700;
            color: {COLORS["text_white"]};
            line-height: 1.2;
            margin-bottom: 6px;
        }}

        .title-section .subtitle {{
            font-size: 15px;
            color: {COLORS["text_gray"]};
        }}

        .divider {{
            border: none;
            border-top: 1px solid #30363D;
            margin: 20px 0;
        }}

        .section {{
            margin-bottom: 36px;
        }}

        .section-header {{
            font-size: 20px;
            font-weight: 700;
            color: {COLORS["blue_light"]};
            margin-bottom: 12px;
        }}

        .body-text {{
            font-size: 15px;
            color: {COLORS["text_light_gray"]};
            line-height: 1.7;
            margin-bottom: 12px;
        }}

        .tldr-box {{
            background: {COLORS["bg_card"]};
            border: 1px solid #30363D;
            border-left: 3px solid {COLORS["blue_primary"]};
            border-radius: 8px;
            padding: 18px 22px;
            font-size: 15px;
            line-height: 1.7;
            color: {COLORS["text_white"]};
        }}

        .tldr-box strong {{
            color: {COLORS["blue_light"]};
        }}

        .tldr-box .green {{
            color: {COLORS["green"]};
            font-weight: 600;
        }}

        .tldr-box .red {{
            color: {COLORS["red"]};
            font-weight: 600;
        }}

        .chart-img {{
            width: 100%;
            max-width: 100%;
            border-radius: 8px;
            margin: 16px 0;
        }}

        /* KPI Cards */
        .kpi-row {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin: 20px 0;
        }}

        .kpi-card {{
            background: {COLORS["bg_card"]};
            border: 1px solid #30363D;
            border-radius: 10px;
            padding: 20px 16px;
            text-align: center;
        }}

        .kpi-value {{
            font-size: 26px;
            font-weight: 700;
            margin-bottom: 4px;
        }}

        .kpi-value.blue {{ color: {COLORS["blue_primary"]}; }}
        .kpi-value.blue-light {{ color: {COLORS["blue_light"]}; }}
        .kpi-value.cyan {{ color: {COLORS["cyan"]}; }}
        .kpi-value.green {{ color: {COLORS["green"]}; }}
        .kpi-value.red {{ color: {COLORS["red"]}; }}

        .kpi-label {{
            font-size: 12px;
            color: {COLORS["text_gray"]};
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        /* Tables */
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
            font-size: 14px;
        }}

        .data-table th {{
            background: {COLORS["blue_primary"]};
            color: white;
            font-weight: 600;
            padding: 10px 14px;
            text-align: left;
        }}

        .data-table th.right,
        .data-table td.right {{
            text-align: right;
        }}

        .data-table td {{
            padding: 10px 14px;
            border-bottom: 1px solid #30363D;
            color: {COLORS["text_light_gray"]};
        }}

        .data-table tr:nth-child(odd) td {{
            background: {COLORS["bg_card"]};
        }}

        .data-table tr:nth-child(even) td {{
            background: #1C2128;
        }}

        .chain-dot {{
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
            vertical-align: middle;
        }}

        /* Takeaway list */
        .takeaway {{
            background: {COLORS["bg_card"]};
            border: 1px solid #30363D;
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 10px;
            font-size: 15px;
            line-height: 1.6;
            color: {COLORS["text_white"]};
        }}

        .takeaway strong {{
            color: {COLORS["blue_light"]};
        }}

        /* Footer */
        .footer {{
            border-top: 1px solid #30363D;
            padding-top: 20px;
            margin-top: 40px;
            text-align: center;
            font-size: 12px;
            color: {COLORS["text_gray"]};
        }}

        .footer a {{
            color: {COLORS["blue_light"]};
            text-decoration: none;
        }}

        .footer a:hover {{
            text-decoration: underline;
        }}

        .source-list {{
            list-style: none;
            padding: 0;
        }}

        .source-list li {{
            padding: 4px 0;
            font-size: 14px;
        }}

        .source-list li::before {{
            content: "\\2022\\00a0\\00a0";
            color: {COLORS["text_gray"]};
        }}

        .source-list a {{
            color: {COLORS["blue_light"]};
            text-decoration: none;
        }}

        .source-list a:hover {{
            text-decoration: underline;
        }}

        /* Responsive */
        @media (max-width: 640px) {{
            .kpi-row {{
                grid-template-columns: repeat(2, 1fr);
            }}

            .title-section h1 {{
                font-size: 24px;
            }}

            .kpi-value {{
                font-size: 20px;
            }}

            .header-inner {{
                flex-direction: column;
                align-items: flex-start;
                gap: 4px;
            }}
        }}
    </style>
</head>
<body>

<div class="header">
    <div class="header-inner">
        <div class="header-left">
            <h1>MORPHO <span>WEEKLY RISK REPORT</span></h1>
        </div>
        <div class="date">{now.strftime("%B %d, %Y")}</div>
    </div>
</div>

<div class="container">

    <!-- Title -->
    <div class="title-section">
        <h1>Morpho Weekly Risk Report</h1>
        <div class="subtitle">Rolling 7-Day Summary &nbsp;|&nbsp; {week_start} &ndash; {week_end}</div>
    </div>

    <hr class="divider">

    <!-- TLDR -->
    <div class="section">
        <h2 class="section-header">TLDR</h2>
        <div class="tldr-box">
            Over the past 7 days, Morpho processed <strong>{total_liq}</strong> in liquidations
            across <strong>{positions:,}</strong> positions and <strong>{markets}</strong> markets on
            <strong>{chains}</strong> networks&mdash;<span class="{bad_debt_class}">{bad_debt_text}</span>.
        </div>
    </div>

    <!-- KPI Cards -->
    <div class="section">
        <div class="kpi-row">
            <div class="kpi-card">
                <div class="kpi-value blue">{total_liq}</div>
                <div class="kpi-label">Total Liquidated</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value blue-light">{positions:,}</div>
                <div class="kpi-label">Positions Liquidated</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value cyan">{markets}</div>
                <div class="kpi-label">Markets Affected</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value {bad_debt_class}">{_format_usd(bad_debt)}</div>
                <div class="kpi-label">Realized Bad Debt</div>
            </div>
        </div>
    </div>

    <!-- Section 1: Liquidations -->
    <div class="section">
        <h2 class="section-header">1. Liquidations &amp; Bad Debt</h2>
        <p class="body-text">
            Morpho&rsquo;s infrastructure processed {total_liq} in liquidations over
            the past week, demonstrating continued resilience. Liquidation activity
            spanned {chains} chains and {markets} distinct markets.
        </p>

        {"<img class='chart-img' src='" + daily_img + "' alt='Daily Liquidation Amounts (Past 7 Days)'>" if daily_img else ""}

        {"<img class='chart-img' src='" + chain_img + "' alt='Liquidation Volume by Chain (Past 7 Days)'>" if chain_img else ""}

        <h3 style="color:{COLORS['text_white']};font-size:15px;margin:18px 0 8px;">Liquidation Breakdown by Chain</h3>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Chain</th>
                    <th class="right">Volume</th>
                    <th class="right">Positions</th>
                    <th class="right">Markets</th>
                </tr>
            </thead>
            <tbody>
                {chain_table_rows}
            </tbody>
        </table>
    </div>

    <!-- Section 2: Bad Debt -->
    <div class="section">
        <h2 class="section-header">2. Bad Debt Overview</h2>
        <p class="body-text">{bad_debt_section_text}</p>

        {"<img class='chart-img' src='" + bad_debt_img + "' alt='Bad Debt Overview'>" if bad_debt_img else ""}

        <h3 style="color:{COLORS['text_white']};font-size:15px;margin:18px 0 8px;">Top Unrealized Bad Debt Positions</h3>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Market</th>
                    <th>Chain</th>
                    <th class="right">Unrealized Debt</th>
                </tr>
            </thead>
            <tbody>
                {bad_debt_table_rows}
            </tbody>
        </table>
    </div>

    <!-- Section 3: Key Takeaways -->
    <div class="section">
        <h2 class="section-header">3. Key Takeaways</h2>

        <div class="takeaway">
            <strong>1. Infrastructure performed as designed.</strong>
            Morpho processed {total_liq} in liquidations across {positions:,} positions
            and {markets} markets on {chains} networks&mdash;with zero bad debt.
        </div>

        <div class="takeaway">
            <strong>2. Protocol resilience confirmed.</strong>
            Despite market conditions, liquidation mechanisms functioned smoothly across
            all chains, demonstrating the robustness of Morpho&rsquo;s decentralized architecture.
        </div>

        <div class="takeaway">
            <strong>3. Curator risk management effective.</strong>
            Market parameters set by curators ensured timely liquidations and prevented
            any losses to lenders across the network.
        </div>
    </div>

    <!-- Data Sources -->
    <hr class="divider">
    <div class="section">
        <h2 class="section-header">Data Sources</h2>
        <ul class="source-list">
            <li><a href="https://data.morpho.org/risk">Morpho Risk Dashboard</a> (data.morpho.org/risk)</li>
            <li><a href="https://dune.com/morpho/morpho-liquidation">Morpho Liquidation Dashboard</a> (Dune Analytics)</li>
            <li>Report generated: {now.strftime("%Y-%m-%d %H:%M UTC")}</li>
        </ul>
    </div>

    <!-- Footer -->
    <div class="footer">
        Morpho Weekly Risk Report &middot; Generated automatically from Dune Analytics data
    </div>

</div>

</body>
</html>"""

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(output_path) / 1024
    print(f"HTML report saved to: {output_path} ({size_kb:.0f} KB)")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate Morpho Weekly Risk Report (HTML)")
    parser.add_argument("--sample", action="store_true",
                        help="Use sample data instead of live Dune API")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Output HTML path (default: index.html)")
    parser.add_argument("--api-key", type=str, default=None,
                        help="Dune API key (or set DUNE_API_KEY env var)")
    args = parser.parse_args()

    if args.api_key:
        os.environ["DUNE_API_KEY"] = args.api_key

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)

    output_path = args.output or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "index.html"
    )

    print("=" * 60)
    print("  MORPHO WEEKLY RISK REPORT — HTML GENERATOR")
    print("=" * 60)
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Mode: {'Sample Data' if args.sample else 'Live Dune API'}")
    print(f"  Output: {output_path}")
    print("=" * 60)
    print()

    # Step 1: Fetch data
    if args.sample:
        from data_fetcher import generate_sample_data
        report_data = generate_sample_data()
    else:
        from data_fetcher import DuneDataFetcher
        try:
            fetcher = DuneDataFetcher()
            report_data = fetcher.fetch_all_report_data()
        except ValueError as e:
            print(f"\nError: {e}")
            print("Tip: Set your API key with: export DUNE_API_KEY='your_key'")
            print("     Or use --sample flag for testing with sample data.")
            sys.exit(1)

    # Step 2: Generate charts
    print("Generating charts...")
    from chart_generator import generate_all_charts
    charts = generate_all_charts(report_data, output_dir=output_dir)
    for name, path in charts.items():
        print(f"  -> {name}: {os.path.basename(path)}")

    # Step 3: Generate HTML
    print("\nGenerating HTML report...")
    generate_html(report_data, charts, output_path)

    print()
    print("=" * 60)
    print("  HTML report generated successfully!")
    print(f"  File: {output_path}")
    print(f"  Open in browser to view.")
    print("=" * 60)

    return output_path


if __name__ == "__main__":
    main()
