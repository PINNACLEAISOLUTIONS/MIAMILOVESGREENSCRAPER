"""
Daily Scraping Script for LandscapeLeadsFL
==========================================
Designed for GitHub Actions CI/CD pipeline.
Runs daily to:
1. Discover & Screen new homeowner leads.
2. Update the cumulative database (docs/leads.json).
"""

import os
import sys
import logging
import asyncio
from datetime import datetime

# Add project root to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LandscapeLeadsFL.agents import ScoutAgent, ScreenerAgent, FormatterAgent

# Configure Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("DailyScrape")


async def run_daily_scan():
    logger.info("🚀 Starting Daily Agentic Scrape...")

    # Initialize Agents (Output to docs/leads for GitHub Pages)
    # Using relative path valid for the repo root execution
    REPO_ROOT = os.getcwd()
    DOCS_OUTPUT_PATH = os.path.join(REPO_ROOT, "docs/leads")

    # 1. Scout (Find Leads)
    # Use mcp=False for reliable automated scraping (Exa/Brave usually require API keys not available in basic CI)
    scout = ScoutAgent(use_mcp=False)
    raw_leads = await scout.discover_leads()

    if not raw_leads:
        logger.warning("No raw leads found. Exiting.")
        return

    # 2. Screener (Filter for Homeowners)
    screener = ScreenerAgent()
    screened_leads = screener.screen(raw_leads)

    if not screened_leads:
        logger.info("No verified homeowner leads found today.")
        return

    # 3. Formatter (Update Dashboard Database)
    logger.info(f"Saving {len(screened_leads)} verified leads to {DOCS_OUTPUT_PATH}...")
    formatter = FormatterAgent()
    formatter.format_output(screened_leads, output_path_base=DOCS_OUTPUT_PATH)

    logger.info("✅ Daily Scrape Complete! Dashboard data updated.")


def main():
    asyncio.run(run_daily_scan())


if __name__ == "__main__":
    main()
