# Morpho Weekly Risk Report Generator

Automated PDF report generator for Morpho's rolling 7-day risk metrics. Pulls live data from Dune Analytics and produces a branded, partner-ready PDF.

## Quick Start

```bash
# 1. Install dependencies
pip install dune-client matplotlib reportlab requests pandas

# 2. Set your Dune API key
export DUNE_API_KEY="your_dune_api_key_here"

# 3. Generate a report
python generate_report.py
```

The PDF will be saved to `./output/morpho_risk_report_YYYY-MM-DD.pdf`.

## Usage

### On-Demand Generation

```bash
# Live data from Dune
python generate_report.py

# Test with sample data (no API key needed)
python generate_report.py --sample

# Custom output path
python generate_report.py --output /path/to/report.pdf
```

### Scheduled Generation

```bash
# Run every Monday at 9 AM UTC (default)
python schedule.py

# Custom cron schedule (e.g., every day at 8 AM)
python schedule.py --cron "0 8 * * *"

# Run once immediately
python schedule.py --once

# With custom output directory
python schedule.py --output-dir /shared/reports/
```

### Cron Job Setup (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add this line for every Monday at 9 AM:
0 9 * * 1 cd /path/to/morpho-report && DUNE_API_KEY="your_key" python generate_report.py
```

## Report Sections

The generated PDF mirrors the structure of the [1/31 liquidity risk summary](https://www.notion.so/morpho-labs/1-31-liquidity-risk-summary-for-growth-2fad69939e6d80f783d0d6ff37bbb658):

1. **TLDR** — One-paragraph executive summary with key numbers
2. **Liquidations & Bad Debt** — Total volume, daily breakdown chart, chain-by-chain breakdown
3. **Bad Debt Overview** — Realized and unrealized bad debt with top positions table
4. **Key Takeaways** — Three concise bullet points for partner communications

## Data Sources

All data is pulled from the Morpho team's public Dune queries:

| Query ID | Description |
|----------|-------------|
| 6024591 | Liquidation Statistics Past 24 Hours |
| 6024779 | Bad Debt Statistics Past 24 Hours |
| 6015286 | Unrealized Bad Debt (Market Level) |
| 6657604 | Bad Debt Events Past 24h |

Plus custom SQL queries against `dune.morpho.result_morpho_liquidation_events` for 7-day rolling aggregations.

## Configuration

Edit `config.py` to customize:

- **Query IDs** — Add or modify Dune query references
- **Custom SQL** — Adjust the rolling window or add new metrics
- **Brand colors** — Update the Morpho color palette
- **Chain colors** — Map new chains to specific colors

## File Structure

```
morpho-report/
├── generate_report.py    # Main entry point
├── schedule.py           # Scheduling / cron wrapper
├── config.py             # Configuration & query IDs
├── data_fetcher.py       # Dune API data fetching
├── chart_generator.py    # Matplotlib chart generation
├── pdf_generator.py      # ReportLab PDF assembly
├── README.md             # This file
└── output/               # Generated reports & charts
```

## Requirements

- Python 3.8+
- Dune API key (from [dune.com](https://dune.com) — free tier works)
- Libraries: `dune-client`, `matplotlib`, `reportlab`, `requests`, `pandas`
