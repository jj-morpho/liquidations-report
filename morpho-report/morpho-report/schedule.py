#!/usr/bin/env python3
"""
Scheduler for the Morpho Weekly Risk Report.
Runs the report generator on a cron-compatible schedule.

Usage:
    # Run continuously (generates report every Monday at 9 AM UTC):
    python schedule.py

    # Run with custom schedule (cron syntax):
    python schedule.py --cron "0 9 * * 1"

    # Run once immediately, then exit:
    python schedule.py --once

    # Run with custom output directory:
    python schedule.py --output-dir /path/to/reports
"""
import os
import sys
import time
import argparse
import subprocess
from datetime import datetime


def run_report(output_dir=None, api_key=None, sample=False):
    """Run the report generator script."""
    cmd = [sys.executable, "generate_report.py"]
    if sample:
        cmd.append("--sample")
    if output_dir:
        date_str = datetime.now().strftime("%Y-%m-%d_%H%M")
        output_path = os.path.join(output_dir, f"morpho_risk_report_{date_str}.pdf")
        cmd.extend(["--output", output_path])
    if api_key:
        cmd.extend(["--api-key", api_key])

    print(f"\n[{datetime.now().isoformat()}] Running report generation...")
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    if result.returncode == 0:
        print(f"[{datetime.now().isoformat()}] Report generated successfully.")
    else:
        print(f"[{datetime.now().isoformat()}] Report generation failed (exit code {result.returncode})")
    return result.returncode


def parse_simple_cron(cron_str):
    """
    Parse a simple cron expression and check if current time matches.
    Format: minute hour day_of_month month day_of_week
    Supports: numbers, * (any), */N (every N)
    """
    parts = cron_str.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron format: {cron_str}")

    now = datetime.now()
    fields = [now.minute, now.hour, now.day, now.month, now.weekday()]
    # Note: cron uses 0=Sunday, Python weekday() uses 0=Monday
    # Convert Python weekday to cron: (weekday + 1) % 7
    fields[4] = (fields[4] + 1) % 7

    for field_val, cron_part in zip(fields, parts):
        if cron_part == "*":
            continue
        elif cron_part.startswith("*/"):
            divisor = int(cron_part[2:])
            if field_val % divisor != 0:
                return False
        elif "," in cron_part:
            allowed = [int(x) for x in cron_part.split(",")]
            if field_val not in allowed:
                return False
        else:
            if field_val != int(cron_part):
                return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Schedule Morpho Risk Report generation")
    parser.add_argument("--cron", type=str, default="0 9 * * 1",
                        help='Cron schedule (default: "0 9 * * 1" = Monday 9 AM)')
    parser.add_argument("--once", action="store_true",
                        help="Run once immediately and exit")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Directory to save reports")
    parser.add_argument("--api-key", type=str, default=None,
                        help="Dune API key")
    parser.add_argument("--sample", action="store_true",
                        help="Use sample data")
    args = parser.parse_args()

    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)

    if args.once:
        sys.exit(run_report(args.output_dir, args.api_key, args.sample))

    print("=" * 60)
    print("  MORPHO REPORT SCHEDULER")
    print("=" * 60)
    print(f"  Schedule: {args.cron}")
    print(f"  Output:   {args.output_dir or 'default'}")
    print(f"  Mode:     {'Sample' if args.sample else 'Live Dune API'}")
    print("=" * 60)
    print("\nWaiting for next scheduled run... (Ctrl+C to stop)")

    last_run_minute = -1
    while True:
        try:
            now = datetime.now()
            current_minute = now.hour * 60 + now.minute
            if current_minute != last_run_minute and parse_simple_cron(args.cron):
                last_run_minute = current_minute
                run_report(args.output_dir, args.api_key, args.sample)
            time.sleep(30)  # Check every 30 seconds
        except KeyboardInterrupt:
            print("\nScheduler stopped.")
            break


if __name__ == "__main__":
    main()
