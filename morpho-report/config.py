"""
Configuration for the Morpho Weekly Risk Report Generator.
Set your DUNE_API_KEY environment variable before running.
"""
import os

# Dune API Configuration
DUNE_API_KEY = os.environ.get("DUNE_API_KEY", "")

# Known Dune Query IDs from the Morpho Liquidation Dashboard
QUERY_IDS = {
    "liquidation_stats_24h": 6024591,      # Liquidation Statistics Past 24 Hours
    "bad_debt_stats_24h": 6024779,          # Bad Debt Statistics Past 24 Hours - Markets
    "unrealized_bad_debt": 6015286,         # Morpho Unrealized Bad Debt
    "bad_debt_events_24h": 6657604,         # Morpho Bad Debt Events - Past 24h
}

# Custom SQL queries for 7-day rolling data
CUSTOM_QUERIES = {
    "weekly_liquidations_by_chain": """
        SELECT
            blockchain,
            SUM(seized_amount_usd) as total_liquidated_usd,
            COUNT(*) as num_liquidations,
            COUNT(DISTINCT market_name) as markets_affected
        FROM dune.morpho.result_morpho_liquidation_events
        WHERE time >= NOW() - INTERVAL '7' DAY
        GROUP BY blockchain
        ORDER BY total_liquidated_usd DESC
    """,
    "daily_liquidations_7d": """
        SELECT
            DATE_TRUNC('day', time) as day,
            blockchain,
            SUM(seized_amount_usd) as total_liquidated_usd,
            COUNT(*) as num_liquidations
        FROM dune.morpho.result_morpho_liquidation_events
        WHERE time >= NOW() - INTERVAL '7' DAY
        GROUP BY 1, 2
        ORDER BY 1 ASC, 2
    """,
    "weekly_bad_debt_by_chain": """
        SELECT
            blockchain,
            SUM(bad_debt_amount_usd) as total_bad_debt_usd,
            COUNT(*) as num_events
        FROM dune.morpho.result_morpho_liquidation_events
        WHERE time >= NOW() - INTERVAL '7' DAY
          AND bad_debt_amount_usd > 0
        GROUP BY blockchain
        ORDER BY total_bad_debt_usd DESC
    """,
    "weekly_liquidation_summary": """
        SELECT
            SUM(seized_amount_usd) as total_liquidated_usd,
            SUM(bad_debt_amount_usd) as total_bad_debt_usd,
            COUNT(*) as total_positions_liquidated,
            COUNT(DISTINCT market_name) as total_markets,
            COUNT(DISTINCT blockchain) as total_chains
        FROM dune.morpho.result_morpho_liquidation_events
        WHERE time >= NOW() - INTERVAL '7' DAY
    """,
}

# Morpho Brand Colors
COLORS = {
    "bg_dark": "#0D1117",
    "bg_card": "#161B22",
    "blue_primary": "#2D7FF9",
    "blue_light": "#58A6FF",
    "blue_accent": "#79C0FF",
    "text_white": "#FFFFFF",
    "text_gray": "#8B949E",
    "text_light_gray": "#C9D1D9",
    "green": "#3FB950",
    "red": "#F85149",
    "yellow": "#D29922",
    "purple": "#BC8CFF",
    "cyan": "#39D2C0",
    "orange": "#F0883E",
    # Chain-specific colors (matching data.morpho.org)
    "chain_ethereum": "#627EEA",
    "chain_base": "#0052FF",
    "chain_polygon": "#8247E5",
    "chain_optimism": "#FF0420",
    "chain_arbitrum": "#28A0F0",
    "chain_hyperevm": "#39D2C0",
    "chain_unichain": "#FF007A",
    "chain_katana": "#D4A843",
    "chain_monad": "#BC8CFF",
    "chain_other": "#8B949E",
}

CHAIN_COLOR_MAP = {
    "ethereum": COLORS["chain_ethereum"],
    "base": COLORS["chain_base"],
    "polygon": COLORS["chain_polygon"],
    "optimism": COLORS["chain_optimism"],
    "arbitrum": COLORS["chain_arbitrum"],
    "hyperevm": COLORS["chain_hyperevm"],
    "unichain": COLORS["chain_unichain"],
    "katana": COLORS["chain_katana"],
    "monad": COLORS["chain_monad"],
}

def get_chain_color(chain_name):
    """Get the brand color for a given chain, with fallback."""
    return CHAIN_COLOR_MAP.get(chain_name.lower(), COLORS["chain_other"])
