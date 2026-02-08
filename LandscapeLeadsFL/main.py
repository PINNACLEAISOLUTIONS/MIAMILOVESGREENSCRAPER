"""
LandscapeLeadsFL - MCP-Enhanced Lead Generation
=================================================
Multi-source lead discovery for landscaping services in South Florida.
Uses MCP integrations for enhanced social media discovery.
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime

from agents import (
    ScoutAgent,
    ScreenerAgent,
    FormatterAgent,
    LeadPipelineOrchestrator,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline_run.log", mode="a"),
    ],
)
logger = logging.getLogger("LandscapeLeadsFL")


async def run_full_pipeline(use_mcp: bool = True) -> dict:
    """
    Run the complete MCP-enhanced lead generation pipeline.

    Args:
        use_mcp: Whether to use MCP integrations (Exa, Brave Search, etc.)

    Returns:
        Summary statistics from the pipeline run
    """
    logger.info("=" * 60)
    logger.info("🌴 LandscapeLeadsFL - MCP-Enhanced Lead Discovery")
    logger.info(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"   MCP Mode: {'Enabled' if use_mcp else 'Disabled'}")
    logger.info("=" * 60)

    # Use the orchestrator for full pipeline
    orchestrator = LeadPipelineOrchestrator(use_mcp=use_mcp)
    summary = await orchestrator.run_full_pipeline()

    return summary


async def run_legacy_pipeline() -> None:
    """
    Run the original (non-MCP) pipeline for backwards compatibility.
    """
    logger.info("Starting LandscapeLeadsFL Lead Generation Workflow (Legacy Mode)...")

    # Initialize Agents (without MCP)
    scout = ScoutAgent(use_mcp=False)
    screener = ScreenerAgent()
    formatter = FormatterAgent()

    # Step 1: Discovery (Scout)
    raw_leads = await scout.discover_leads()

    if not raw_leads:
        logger.warning("No raw leads found during discovery phase.")
        return

    # Step 2: Filtering (Screener)
    screened_leads = screener.screen(raw_leads)

    if not screened_leads:
        logger.warning("No leads passed the screening criteria.")
        return

    # Step 3: Output (Formatter)
    try:
        formatter.format_output(screened_leads)
        logger.info("LandscapeLeadsFL: Workflow completed successfully!")
    except Exception as e:
        logger.error(f"Error saving files to C:/Users/futur/gemini_workspace: {e}")
        logger.info("Attempting local file save fallback...")
        formatter.format_output(screened_leads, output_path_base="./leads")


async def generate_mcp_queries() -> None:
    """
    Generate MCP queries without running scrapers.
    Useful for manual or n8n-based execution.
    """
    logger.info("Generating MCP Search Queries...")

    orchestrator = LeadPipelineOrchestrator(use_mcp=True)
    instructions = orchestrator.get_mcp_instructions()

    print("\n" + instructions)

    # Save to file
    with open("C:/Users/futur/gemini_workspace/mcp_instructions.md", "w") as f:
        f.write(instructions)

    logger.info(
        "MCP instructions saved to C:/Users/futur/gemini_workspace/mcp_instructions.md"
    )


def main():
    """
    Main entry point with CLI argument support.
    """
    parser = argparse.ArgumentParser(
        description="LandscapeLeadsFL - MCP-Enhanced Lead Discovery"
    )
    parser.add_argument(
        "--mode",
        choices=["full", "legacy", "queries"],
        default="full",
        help="Pipeline mode: 'full' (MCP-enhanced), 'legacy' (original), 'queries' (generate MCP queries only)",
    )
    parser.add_argument(
        "--no-mcp",
        action="store_true",
        help="Disable MCP integrations (same as --mode legacy)",
    )

    args = parser.parse_args()

    if args.mode == "queries":
        asyncio.run(generate_mcp_queries())
    elif args.mode == "legacy" or args.no_mcp:
        asyncio.run(run_legacy_pipeline())
    else:
        summary = asyncio.run(run_full_pipeline(use_mcp=True))

        # Print final summary
        print("\n" + "=" * 60)
        print("📊 FINAL SUMMARY")
        print("=" * 60)
        for key, value in summary.items():
            print(f"   {key}: {value}")
        print("=" * 60)


if __name__ == "__main__":
    main()
