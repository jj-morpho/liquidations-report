"""
Data fetching module for Morpho risk reports.
Pulls data from Dune Analytics API.
"""
import json
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from config import DUNE_API_KEY, QUERY_IDS, CUSTOM_QUERIES


class DuneDataFetcher:
    """Fetches data from Dune Analytics API."""

    BASE_URL = "https://api.dune.com/api/v1"

    def __init__(self, api_key=None):
        self.api_key = api_key or DUNE_API_KEY
        if not self.api_key:
            raise ValueError(
                "DUNE_API_KEY not set. Export it as an environment variable "
                "or pass it to DuneDataFetcher(api_key='...')"
            )
        self.headers = {
            "x-dune-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def get_latest_result(self, query_id):
        """Fetch the latest cached result for a known query."""
        url = f"{self.BASE_URL}/query/{query_id}/results"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        data = resp.json()
        rows = data.get("result", {}).get("rows", [])
        return pd.DataFrame(rows) if rows else pd.DataFrame()

    def execute_sql(self, sql, poll_interval=2, max_wait=120):
        """Execute a raw SQL query and wait for results."""
        url = f"{self.BASE_URL}/query/execute/sql"
        payload = {"query_sql": sql}
        resp = requests.post(url, headers=self.headers, json=payload)
        resp.raise_for_status()
        execution_id = resp.json().get("execution_id")

        if not execution_id:
            raise RuntimeError("No execution_id returned from Dune")

        # Poll for results
        status_url = f"{self.BASE_URL}/execution/{execution_id}/status"
        result_url = f"{self.BASE_URL}/execution/{execution_id}/results"
        waited = 0

        while waited < max_wait:
            time.sleep(poll_interval)
            waited += poll_interval
            status_resp = requests.get(status_url, headers=self.headers)
            status_resp.raise_for_status()
            state = status_resp.json().get("state", "")
            if state == "QUERY_STATE_COMPLETED":
                result_resp = requests.get(result_url, headers=self.headers)
                result_resp.raise_for_status()
                rows = result_resp.json().get("result", {}).get("rows", [])
                return pd.DataFrame(rows) if rows else pd.DataFrame()
            elif state in ("QUERY_STATE_FAILED", "QUERY_STATE_CANCELLED"):
                error = status_resp.json().get("error", "Unknown error")
                raise RuntimeError(f"Query failed: {error}")

        raise TimeoutError(f"Query did not complete within {max_wait}s")

    def fetch_all_report_data(self):
        """Fetch all data needed for the weekly risk report."""
        print("Fetching Morpho weekly risk report data from Dune...")
        report_data = {}

        # 1. Fetch weekly liquidation summary
        print("  -> Weekly liquidation summary...")
        try:
            report_data["weekly_summary"] = self.execute_sql(
                CUSTOM_QUERIES["weekly_liquidation_summary"]
            )
        except Exception as e:
            print(f"     Warning: {e}")
            report_data["weekly_summary"] = pd.DataFrame()

        # 2. Fetch daily liquidations for 7-day chart
        print("  -> Daily liquidations (7d)...")
        try:
            report_data["daily_liquidations"] = self.execute_sql(
                CUSTOM_QUERIES["daily_liquidations_7d"]
            )
        except Exception as e:
            print(f"     Warning: {e}")
            report_data["daily_liquidations"] = pd.DataFrame()

        # 3. Fetch weekly liquidations by chain
        print("  -> Liquidations by chain...")
        try:
            report_data["liquidations_by_chain"] = self.execute_sql(
                CUSTOM_QUERIES["weekly_liquidations_by_chain"]
            )
        except Exception as e:
            print(f"     Warning: {e}")
            report_data["liquidations_by_chain"] = pd.DataFrame()

        # 4. Fetch weekly bad debt by chain
        print("  -> Bad debt by chain...")
        try:
            report_data["bad_debt_by_chain"] = self.execute_sql(
                CUSTOM_QUERIES["weekly_bad_debt_by_chain"]
            )
        except Exception as e:
            print(f"     Warning: {e}")
            report_data["bad_debt_by_chain"] = pd.DataFrame()

        # 5. Fetch existing dashboard queries for snapshot data
        for name, qid in QUERY_IDS.items():
            print(f"  -> Dashboard query: {name}...")
            try:
                report_data[name] = self.get_latest_result(qid)
            except Exception as e:
                print(f"     Warning: {e}")
                report_data[name] = pd.DataFrame()

        print("Data fetch complete.\n")
        return report_data


def generate_sample_data():
    """Generate realistic sample data for testing without a Dune API key."""
    from datetime import datetime, timedelta
    import random

    now = datetime.now()
    report_data = {}

    # Weekly summary
    report_data["weekly_summary"] = pd.DataFrame([{
        "total_liquidated_usd": 2_847_321.45,
        "total_bad_debt_usd": 0.0,
        "total_positions_liquidated": 1247,
        "total_markets": 89,
        "total_chains": 11,
    }])

    # Daily liquidations over 7 days
    chains = ["ethereum", "base", "polygon", "arbitrum", "optimism", "hyperevm"]
    daily_rows = []
    for i in range(7):
        day = now - timedelta(days=6 - i)
        for chain in chains:
            base_amount = random.uniform(30_000, 400_000) if chain in ["ethereum", "base"] else random.uniform(5_000, 80_000)
            daily_rows.append({
                "day": day.strftime("%Y-%m-%d 00:00:00"),
                "blockchain": chain,
                "total_liquidated_usd": base_amount,
                "num_liquidations": random.randint(10, 200),
            })
    report_data["daily_liquidations"] = pd.DataFrame(daily_rows)

    # Liquidations by chain
    chain_rows = []
    for chain in chains:
        total = random.uniform(100_000, 1_200_000) if chain in ["ethereum", "base"] else random.uniform(10_000, 200_000)
        chain_rows.append({
            "blockchain": chain,
            "total_liquidated_usd": total,
            "num_liquidations": random.randint(50, 600),
            "markets_affected": random.randint(5, 40),
        })
    report_data["liquidations_by_chain"] = pd.DataFrame(chain_rows).sort_values(
        "total_liquidated_usd", ascending=False
    )

    # Bad debt by chain (zero for most)
    report_data["bad_debt_by_chain"] = pd.DataFrame()

    # Liquidation stats 24h
    report_data["liquidation_stats_24h"] = pd.DataFrame([{
        "total_liquidated": 60173,
        "positions_liquidated": 285,
        "markets_liquidated": 18,
        "chains_liquidated": 6,
    }])

    # Bad debt stats 24h
    report_data["bad_debt_stats_24h"] = pd.DataFrame([{
        "total_bad_debt_amount": 0,
        "markets_with_bad_debt": 0,
        "chains_with_bad_debt": 0,
    }])

    # Unrealized bad debt
    report_data["unrealized_bad_debt"] = pd.DataFrame([
        {"market": "deUSD/USDC(86.0%)", "chain": "ethereum", "unrealized_bad_debt": 5762.19, "total_supply": 10004.95},
        {"market": "UNKNOWN/lvlUSD(91.5%)", "chain": "ethereum", "unrealized_bad_debt": 5261.65, "total_supply": 5267.03},
        {"market": "wbCOIN/USDC(86.0%)", "chain": "base", "unrealized_bad_debt": 3647.55, "total_supply": 21853.78},
    ])

    # Bad debt events
    report_data["bad_debt_events_24h"] = pd.DataFrame()

    return report_data


if __name__ == "__main__":
    # Quick test
    if DUNE_API_KEY:
        fetcher = DuneDataFetcher()
        data = fetcher.fetch_all_report_data()
        for key, df in data.items():
            print(f"{key}: {len(df)} rows")
    else:
        print("No DUNE_API_KEY set. Using sample data...")
        data = generate_sample_data()
        for key, df in data.items():
            print(f"{key}: {len(df)} rows")
            if not df.empty:
                print(df.head(3).to_string())
            print()
