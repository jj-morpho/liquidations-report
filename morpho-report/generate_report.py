#!/usr/bin/env python3
"""
Morpho Weekly Risk Report Generator
====================================
Generates a branded PDF report with rolling 7-day risk metrics.

Usage:
    # With live Dune data:
    export DUNE_API_KEY="your_api_key_here"
    python generate_report.py

    # With sample data (for testing):
    python generate_report.py --sample

    # Custom output path:
    python generate_report.py --output /path/to/report.pdf
"""
import os
import sys
import argparse
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="Generate Morpho Weekly Risk Report")
    parser.add_argument("--sample", action="store_true",
                        help="Use sample data instead of live Dune API")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Output PDF path (default: auto-generated)")
    parser.add_argument("--api-key", type=str, default=None,
                        help="Dune API key (or set DUNE_API_KEY env var)")
    args = parser.parse_args()

    # Set API key if provided
    if args.api_key:
        os.environ["DUNE_API_KEY"] = args.api_key

    # Create output directory
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)

    # Generate output filename with date
    if args.output:
        output_path = args.output
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_path = os.path.join(output_dir, f"morpho_risk_report_{date_str}.pdf")

    print("=" * 60)
    print("  MORPHO WEEKLY RISK REPORT GENERATOR")
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
        if isinstance(path, dict):
            for vname, vpath in path.items():
                print(f"  -> {name}/{vname}: {os.path.basename(vpath)}")
        else:
            print(f"  -> {name}: {os.path.basename(path)}")

    # Step 3: Generate PDF
    print("\nGenerating PDF report...")
    from pdf_generator import generate_report
    generate_report(report_data, charts, output_path)

    print()
    print("=" * 60)
    print(f"  Report generated successfully!")
    print(f"  File: {output_path}")
    print(f"  Size: {os.path.getsize(output_path) / 1024:.1f} KB")
    print("=" * 60)

    return output_path


if __name__ == "__main__":
    main()
