"""
MCP-Enhanced Lead Generation Agents
=====================================
Multi-agent architecture for homeowner lead discovery using:
- Scout Agent: MCP-powered discovery across social platforms
- Screener Agent: Intent validation and professional filtering
- Formatter Agent: Cumulative lead database management
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime

import pandas as pd  # type: ignore

from scrapers import (
    MiamiDadeScraper,
    BrowardScraper,
    CraigslistScraper,
    GoogleSearchNavigator,
)
from mcp_integrations import (
    MCPLeadAggregator,
    ExaSearchIntegration,
    BraveSearchIntegration,
)

logger = logging.getLogger(__name__)


class ScoutAgent:
    """
    The Scout: Discovers homeowner-centric landscape project opportunities.
    Now enhanced with MCP integrations for social media discovery.
    """

    def __init__(self, use_mcp: bool = True):
        self.use_mcp = use_mcp

        # Traditional scrapers
        self.miami_scraper = MiamiDadeScraper()
        self.broward_scraper = BrowardScraper()
        self.craigslist_scraper = CraigslistScraper()
        self.google_scraper = GoogleSearchNavigator()

        # MCP-enhanced scrapers
        if use_mcp:
            self.mcp_aggregator = MCPLeadAggregator()
            self.exa_integration = ExaSearchIntegration()
            self.brave_integration = BraveSearchIntegration()

    async def discover_leads(self) -> list[dict]:
        """
        Discover leads from all sources (traditional + MCP-enhanced).
        """
        logger.info("🔍 Scout Agent: Beginning Multi-Source Discovery...")
        results = []

        # Run traditional scrapers in parallel
        traditional_tasks = [
            self.craigslist_scraper.scrape(),
            self.google_scraper.scrape(),
            self.miami_scraper.scrape(),
            self.broward_scraper.scrape(),
        ]

        traditional_results = await asyncio.gather(
            *traditional_tasks, return_exceptions=True
        )

        for result in traditional_results:
            if isinstance(result, list):
                results.extend(result)
            elif isinstance(result, Exception):
                logger.warning(f"Traditional scraper error: {result}")

        logger.info(f"   📋 Traditional sources: {len(results)} leads")

        # Run MCP-enhanced discovery
        if self.use_mcp:
            try:
                mcp_leads = await self.mcp_aggregator.run_discovery()
                # Convert Lead objects to dicts for consistency
                for lead in mcp_leads:
                    results.append(lead.to_dict())
                logger.info(f"   🌐 MCP sources: {len(mcp_leads)} leads")
            except Exception as e:
                logger.warning(f"MCP discovery error: {e}")

        logger.info(f"✅ Scout Agent: Gathered {len(results)} total raw leads.")
        return results

    def get_mcp_queries(self) -> dict:
        """
        Get generated MCP queries for manual or automated execution.
        Returns queries formatted for Exa and Brave Search MCPs.
        """
        if not self.use_mcp:
            return {}

        return {
            "exa_queries": self.exa_integration.generate_search_queries(),
            "brave_queries": self.brave_integration.generate_dork_queries(),
            "usage_instructions": {
                "exa": "Use 'web_search_exa' or 'deep_search_exa' MCP tools",
                "brave": "Use Brave Search MCP with dork query format",
                "example_prompt": "Search for homeowners in Miami looking for landscaping services on Reddit",
            },
        }


class ScreenerAgent:
    """
    The Screener: Enforces Homeowner-Only intent and filters out landscaping services.
    Enhanced with stricter professional detection and scoring.
    """

    def __init__(self):
        self.target_cities = [
            "broward",
            "miami",
            "fort lauderdale",
            "dade",
            "coral gables",
            "weston",
            "davie",
            "plantation",
            "sunrise",
            "boca",
            "parkland",
            "pompano",
            "hollywood",
            "delray",
            "palm beach",
        ]

        # Professional/service provider indicators to EXCLUDE
        self.pro_bad_words = [
            "we provide",
            "our company",
            "professional price",
            "free estimate",
            "licensed and insured",
            "best prices",
            "service provided",
            "installation masters",
            "call for quote",
            "family owned",
            "licensed company",
            "we install",
            "our team",
            "years of experience",
            "serving",
            "satisfaction guaranteed",
            "fully insured",
            "bonded",
            "commercial and residential",
            "visit our website",
            "dm for quote",
            "affordable rates",
            "accept credit cards",
            "financing available",
        ]

        # Sales/spam indicators to EXCLUDE
        self.sales_flags = [
            "selling",
            "for sale",
            "available for purchase",
            "---",
            "buy now",
            "discount",
            "limited time",
            "special offer",
        ]

    def screen(self, raw_leads: list[dict]) -> list[dict]:
        """
        Validate resident intent and filter out professional advertisements.
        Returns only high-confidence homeowner leads.
        """
        logger.info("🔎 Screener Agent: Validating Resident Intent...")
        filtered_leads = []

        for lead in raw_leads:
            text = str(lead.get("Raw_Text", "")).lower()
            title = str(lead.get("Job_Title", "")).lower()
            combined = f"{title} {text}"

            # EXCLUSION 1: Professional service providers
            if any(f in combined for f in self.pro_bad_words):
                continue

            # EXCLUSION 2: Sales/spam posts
            if any(sf in combined for sf in self.sales_flags):
                continue

            # SCORING: Calculate homeowner intent confidence
            score = self._calculate_intent_score(combined)

            # Threshold: Must have high intent confidence
            if score >= 25:
                lead["Score"] = score
                lead["Screened_At"] = datetime.now().isoformat()
                filtered_leads.append(lead)

        logger.info(
            f"✅ Screener Agent: {len(filtered_leads)} verified homeowners passed."
        )
        return filtered_leads

    def _calculate_intent_score(self, text: str) -> int:
        """
        Calculate homeowner intent score based on linguistic patterns.
        Higher score = more likely to be a genuine homeowner request.
        """
        score = 0

        # Personal pronouns (strong homeowner signal)
        if any(
            re.search(pat, text)
            for pat in [
                r"\bi\b",
                r"\bmy\b",
                r"\bme\b",
                r"\bour yard\b",
                r"\bmy home\b",
                r"\bmy property\b",
                r"\bmy lawn\b",
                r"\bour house\b",
            ]
        ):
            score += 25

        # Seeking help language
        if any(
            re.search(pat, text)
            for pat in [
                r"\bneed\b",
                r"\blooking for\b",
                r"\bhire\b",
                r"\bhelp\b",
                r"\brecommend\b",
                r"\bseeking\b",
                r"\bwant\b",
            ]
        ):
            score += 15

        # Specific project mentions (high intent)
        project_keywords = [
            "sod",
            "paver",
            "drainage",
            "design",
            "installation",
            "overhaul",
            "irrigation",
            "hedge",
            "tree removal",
            "fence",
            "patio",
            "deck",
        ]
        if any(kw in text for kw in project_keywords):
            score += 10

        # Location mentions (verifies local)
        if any(city in text for city in self.target_cities):
            score += 5

        # Question patterns (likely seeking help)
        if any(
            pat in text for pat in ["?", "anyone know", "can anyone", "does anyone"]
        ):
            score += 5

        return score


class FormatterAgent:
    """
    The Formatter: Manages the Cumulative Homeowner Project Database.
    Enhanced with MCP source tracking and deduplication.
    """

    def format_output(
        self,
        screened_leads: list[dict],
        output_path_base: str = "C:/Users/futur/gemini_workspace/leads",
    ) -> tuple[str, str] | None:
        """
        Format and save leads to JSON and CSV, merging with existing database.
        """
        if not screened_leads:
            logger.info("Formatter Agent: No new homeowner leads to format.")
            return None

        json_path = f"{output_path_base}.json"
        csv_path = f"{output_path_base}.csv"

        # Load existing leads database
        existing_leads = []
        if os.path.exists(json_path):
            try:
                with open(json_path, "r") as f:
                    content = f.read().strip()
                    if content:
                        existing_leads = json.loads(content)
            except Exception as e:
                logger.warning(f"Could not load existing leads: {e}")

        # Combine and deduplicate
        all_leads = screened_leads + existing_leads

        # Final scrub: Remove any sneaky professional ads
        clean_leads = self._final_scrub(all_leads)

        # Deduplicate by URL
        dedup_map = {lead["Source_URL"]: lead for lead in clean_leads}
        final_list = list(dedup_map.values())

        # Sort by score (highest first)
        final_list.sort(key=lambda x: x.get("Score", 0), reverse=True)

        # Save outputs
        with open(json_path, "w") as f:
            json.dump(final_list, f, indent=2)

        # CSV with clean columns
        df = pd.DataFrame(final_list)
        if not df.empty:
            # Select and order columns for CSV
            csv_columns = [
                "Job_Title",
                "Source_URL",
                "Score",
                "Source_Platform",
                "Closing_Date",
                "Agency",
                "Screened_At",
            ]
            available_cols = [c for c in csv_columns if c in df.columns]
            df[available_cols].to_csv(csv_path, index=False)

        logger.info(
            f"✅ Formatter Agent: Homeowner Project Portal now tracking "
            f"{len(final_list)} verified projects."
        )
        return csv_path, json_path

    def _final_scrub(self, leads: list[dict]) -> list[dict]:
        """Final pass to remove any professional ads that slipped through."""
        pro_flags = [
            "free estimate",
            "licensed and insured",
            "our company",
            "we provide",
            "call us today",
            "years of experience",
        ]

        clean_leads = []
        for lead in leads:
            text = str(lead.get("Raw_Text", "")).lower()
            if not any(f in text for f in pro_flags):
                clean_leads.append(lead)

        return clean_leads


class LeadPipelineOrchestrator:
    """
    Orchestrator: Runs the full lead discovery pipeline.
    Coordinates Scout, Screener, and Formatter agents.
    """

    def __init__(self, use_mcp: bool = True):
        self.scout = ScoutAgent(use_mcp=use_mcp)
        self.screener = ScreenerAgent()
        self.formatter = FormatterAgent()

    async def run_full_pipeline(self) -> dict:
        """
        Execute the complete lead generation pipeline.
        Returns summary statistics.
        """
        logger.info("=" * 60)
        logger.info("🚀 LEAD PIPELINE STARTING")
        logger.info("=" * 60)

        # Phase 1: Discovery
        raw_leads = await self.scout.discover_leads()

        # Phase 2: Screening
        screened_leads = self.screener.screen(raw_leads)

        # Phase 3: Formatting & Storage
        output = self.formatter.format_output(screened_leads)

        # Generate summary
        summary = {
            "run_timestamp": datetime.now().isoformat(),
            "raw_leads_found": len(raw_leads),
            "verified_leads": len(screened_leads),
            "conversion_rate": f"{(len(screened_leads) / max(len(raw_leads), 1)) * 100:.1f}%",
            "output_files": output,
        }

        logger.info("\n" + "=" * 60)
        logger.info("📊 PIPELINE COMPLETE")
        logger.info(f"   Raw Leads: {summary['raw_leads_found']}")
        logger.info(f"   Verified Leads: {summary['verified_leads']}")
        logger.info(f"   Conversion Rate: {summary['conversion_rate']}")
        logger.info("=" * 60)

        return summary

    def get_mcp_instructions(self) -> str:
        """
        Get instructions for using MCP tools for lead discovery.
        """
        queries = self.scout.get_mcp_queries()

        instructions = """
# MCP Lead Discovery Instructions

## Available MCP Tools

### 1. Exa MCP (Best for Semantic Search)
Use `web_search_exa` or `deep_search_exa` with queries like:
"""
        for q in queries.get("exa_queries", [])[:5]:
            instructions += f'- "{q}"\n'

        instructions += """
### 2. Brave Search MCP (Best for Discovery Dorks)
Use Brave Search with these dork queries:
"""
        for dq in queries.get("brave_queries", [])[:5]:
            instructions += f"- {dq.get('query', '')}\n"

        instructions += """
### 3. Reddit MCP (Most Reliable for Homeowner Requests)
Read specific subreddits via Reddit API:
- r/forhire
- r/HireAHelper  
- r/HomeImprovement
- r/Miami
- r/landscaping

### Example Agent Prompts

**For Exa MCP:**
"Search Reddit for Miami homeowners looking for landscaping services using web_search_exa"

**For Brave Search:**
"Use Brave Search to find: site:reddit.com/r/forhire 'landscaping' 'miami' 'hiring'"

**For Deep Research:**
"Use deep_search_exa to research South Florida landscaping demand and homeowner pain points"
"""
        return instructions


# Export for backwards compatibility
__all__ = [
    "ScoutAgent",
    "ScreenerAgent",
    "FormatterAgent",
    "LeadPipelineOrchestrator",
]
