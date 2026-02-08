"""
MCP Integrations for Lead Generation
=====================================
Connects to various MCP servers for enhanced web scraping and lead discovery:
- Exa MCP: Semantic search, deep research, company research
- Brave Search MCP: Discovery via "dork" queries
- Browser Automation: Puppeteer/Playwright for deep extraction
"""

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from patchright.async_api import async_playwright  # type: ignore
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Lead:
    """Standardized lead format across all scrapers."""

    source_url: str
    job_title: str
    agency: str
    closing_date: str
    raw_text: str
    source_platform: str
    discovered_at: str = ""
    score: int = 0

    def __post_init__(self):
        if not self.discovered_at:
            self.discovered_at = datetime.now().isoformat()

    def to_dict(self):
        return {
            "Source_URL": self.source_url,
            "Job_Title": self.job_title,
            "Agency": self.agency,
            "Closing_Date": self.closing_date,
            "Raw_Text": self.raw_text,
            "Source_Platform": self.source_platform,
            "Discovered_At": self.discovered_at,
            "Score": self.score,
        }


class ExaSearchIntegration:
    """
    Integration with Exa MCP for semantic search across social platforms.
    Uses web_search_exa and deep_search_exa for finding homeowner leads.
    """

    def __init__(self):
        self.target_regions = [
            "miami",
            "broward",
            "fort lauderdale",
            "dade",
            "coral gables",
            "weston",
            "davie",
            "plantation",
            "sunrise",
            "boca",
            "parkland",
            "palm beach",
            "pompano",
            "hollywood fl",
        ]
        self.service_keywords = [
            "pavers",
            "sod installation",
            "artificial turf",
            "landscaping",
            "landscaping needed",
            "yard renovation",
            "tree removal",
            "travertine",
            "driveway pavers",
            "patio installation",
            "hardscape",
            "new lawn",
            "re-sod",
            "tree cutting",
            "pool deck",
        ]

    def generate_search_queries(self) -> list[str]:
        """Generate optimized search queries for Exa semantic search."""
        queries = []

        # Calculate date for 30 days ago
        last_month = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        # Reddit-focused queries
        for region in self.target_regions[:5]:  # Limit regions per run
            queries.extend(
                [
                    f'site:reddit.com "{region}" "looking for" landscaper OR "need landscaping" after:{last_month}',
                    f'site:reddit.com/r/forhire "{region}" landscaping OR "yard work" after:{last_month}',
                    f'site:reddit.com/r/HomeImprovement "{region}" recommend landscaper after:{last_month}',
                    f'site:reddit.com "{region}" "hire" "lawn" OR "garden" after:{last_month}',
                ]
            )

        # Nextdoor-focused queries (indexed by search engines)
        for region in self.target_regions[:3]:
            queries.extend(
                [
                    f'site:nextdoor.com "{region}" "recommendation" landscaper after:{last_month}',
                    f'site:nextdoor.com "{region}" "looking for" "yard work" after:{last_month}',
                ]
            )

        # Twitter/X-focused queries
        for region in self.target_regions[:3]:
            queries.extend(
                [
                    f'site:twitter.com "{region}" "looking for" "landscaper" -retweets',
                    f'site:x.com "{region}" "need help" "yard" OR "lawn"',
                ]
            )

        # Facebook/Marketplace queries (public posts)
        for region in self.target_regions[:3]:
            queries.extend(
                [
                    f'site:facebook.com/marketplace "{region}" landscaping service wanted',
                    f'site:facebook.com "{region}" "hiring" landscaper',
                ]
            )

        return queries


class BraveSearchIntegration:
    """
    Integration with Brave Search for discovery via "dork" queries.
    More effective than direct scraping for platforms that block bots.
    """

    def __init__(self):
        self.dork_templates = {
            "reddit_hiring": 'site:reddit.com/r/forhire "{keyword}" "{location}" hiring',
            "reddit_recommend": 'site:reddit.com "{location}" "recommend" "{keyword}"',
            "twitter_looking": 'site:twitter.com "{location}" "looking for" "{keyword}" -retweets',
            "nextdoor_need": 'site:nextdoor.com "{location}" "need" "{keyword}"',
            "facebook_wanted": 'site:facebook.com "{location}" "{keyword}" wanted',
            "yelp_request": 'site:yelp.com "{location}" "{keyword}" quote request',
        }

        self.locations = [
            "Miami",
            "Fort Lauderdale",
            "Broward",
            "Coral Gables",
            "Weston",
            "Davie",
            "Plantation",
            "Boca Raton",
        ]

        self.keywords = [
            "pavers",
            "sod",
            "landscaping",
            "landscaping needed",
            "tree removal",
            "artificial grass",
            "travertine",
            "driveway",
            "patio",
            "hardscaping",
            "tree cutting",
        ]

    def generate_dork_queries(self) -> list[dict]:
        """Generate Brave Search dork queries with metadata."""
        queries = []

        for template_name, template in self.dork_templates.items():
            for location in self.locations[:4]:  # Limit per run
                for keyword in self.keywords[:5]:
                    query = template.format(location=location, keyword=keyword)
                    queries.append(
                        {
                            "query": query,
                            "template": template_name,
                            "location": location,
                            "keyword": keyword,
                        }
                    )

        return queries


class SocialMediaScraper:
    """
    Advanced social media scraper using browser automation for deep extraction.
    Handles TikTok comments, X threads, and Reddit posts.
    """

    def __init__(self):
        self.rate_limit_delay = (3, 8)  # Random delay range in seconds
        self.max_pages_per_session = 10
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        ]

    async def _get_browser_context(self, playwright):
        """Create a stealth browser context."""
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=random.choice(self.user_agents),
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York",
        )
        return browser, context

    async def _human_behavior(self, page):
        """Simulate human-like behavior to avoid detection."""
        # Random mouse movements
        await page.mouse.move(random.randint(100, 800), random.randint(100, 600))
        await asyncio.sleep(random.uniform(0.5, 1.5))

        # Random scrolling
        scroll_amount = random.randint(200, 600)
        await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        await asyncio.sleep(random.uniform(1, 2))

    async def scrape_reddit_posts(
        self, subreddits: list[str], keywords: list[str]
    ) -> list[Lead]:
        """Scrape Reddit for homeowner posts in relevant subreddits."""
        leads = []

        target_subreddits = subreddits or [
            "r/forhire",
            "r/HireAHelper",
            "r/Miami",
            "r/fortlauderdale",
            "r/HomeImprovement",
            "r/landscaping",
            "r/gardening",
        ]

        search_keywords = keywords or [
            "landscaping",
            "yard work",
            "lawn care",
            "need help",
            "looking for",
            "recommendation",
            "sod",
            "pavers",
        ]

        async with async_playwright() as p:
            browser, context = await self._get_browser_context(p)
            page = await context.new_page()

            try:
                for subreddit in target_subreddits[:5]:  # Limit per session
                    for keyword in search_keywords[:3]:
                        await asyncio.sleep(random.uniform(*self.rate_limit_delay))

                        # Use old.reddit.com for simpler HTML parsing
                        url = f"https://old.reddit.com/{subreddit}/search?q={keyword.replace(' ', '+')}&restrict_sr=on&sort=new"

                        try:
                            await page.goto(
                                url, wait_until="domcontentloaded", timeout=30000
                            )
                            await self._human_behavior(page)

                            # Extract posts
                            posts = await page.query_selector_all(".search-result")

                            for post in posts[:5]:  # Limit posts per search
                                title_el = await post.query_selector("a.search-title")
                                if not title_el:
                                    continue

                                title = await title_el.inner_text()
                                link = await title_el.get_attribute("href")

                                # Check for homeowner intent
                                if await self._is_homeowner_intent(title, ""):
                                    leads.append(
                                        Lead(
                                            source_url=link or "",
                                            job_title=title,
                                            agency="Reddit Community",
                                            closing_date="Ongoing",
                                            raw_text=f"Reddit post: {title}",
                                            source_platform="Reddit",
                                        )
                                    )

                        except Exception as e:
                            logger.warning(f"Reddit scrape error for {subreddit}: {e}")
                            continue

            finally:
                await browser.close()

        return leads

    async def scrape_tiktok_comments(self, video_urls: list[str]) -> list[Lead]:
        """
        Scrape TikTok video comments for potential landscaping service requests.
        WARNING: TikTok is aggressive with bot detection. Use sparingly.
        """
        leads = []

        async with async_playwright() as p:
            browser, context = await self._get_browser_context(p)
            page = await context.new_page()

            try:
                for url in video_urls[:3]:  # Strict limit
                    await asyncio.sleep(
                        random.uniform(5, 10)
                    )  # Longer delay for TikTok

                    try:
                        await page.goto(url, wait_until="networkidle", timeout=45000)
                        await self._human_behavior(page)

                        # Scroll to load comments
                        for _ in range(3):
                            await page.evaluate("window.scrollBy(0, 500)")
                            await asyncio.sleep(1)

                        # Extract comment text (TikTok structure varies)
                        comments = await page.query_selector_all(
                            '[class*="comment-text"]'
                        )

                        for comment in comments[:10]:
                            text = await comment.inner_text()
                            if await self._is_homeowner_intent("", text):
                                leads.append(
                                    Lead(
                                        source_url=url,
                                        job_title=f"TikTok Comment Lead: {text[:50]}...",
                                        agency="TikTok Discovery",
                                        closing_date="ASAP",
                                        raw_text=text,
                                        source_platform="TikTok",
                                    )
                                )

                    except Exception as e:
                        logger.warning(f"TikTok scrape error: {e}")
                        continue

            finally:
                await browser.close()

        return leads

    async def _is_homeowner_intent(self, title: str, text: str) -> bool:
        """Determine if content indicates homeowner (not professional) intent."""
        combined = f"{title} {text}".lower()

        # Homeowner signals
        homeowner_patterns = [
            r"\bi\b",
            r"\bmy\b",
            r"\bme\b",
            r"\bneed\b",
            r"\bhelp\b",
            r"\blooking for\b",
            r"\bhire\b",
            r"\brecommend\b",
            r"\bour yard\b",
            r"\bmy house\b",
            r"\bmy lawn\b",
        ]

        # Professional signals (exclude these)
        pro_patterns = [
            "we provide",
            "our company",
            "licensed and insured",
            "free estimate",
            "professional",
            "call us",
            "our team",
            "years of experience",
            "serving",
            "family owned",
        ]

        is_homeowner = any(re.search(p, combined) for p in homeowner_patterns)
        is_professional = any(p in combined for p in pro_patterns)

        return is_homeowner and not is_professional


class MCPLeadAggregator:
    """
    Aggregates leads from all MCP-integrated sources.
    Orchestrates Exa semantic search, Brave dork queries, and browser automation.
    """

    def __init__(self):
        self.exa = ExaSearchIntegration()
        self.brave = BraveSearchIntegration()
        self.social = SocialMediaScraper()
        self.output_dir = "C:/Users/futur/gemini_workspace"

    async def run_discovery(self) -> list[Lead]:
        """
        Run full lead discovery pipeline across all MCP sources.
        Returns aggregated, deduplicated leads.
        """
        logger.info("🚀 Starting MCP-Integrated Lead Discovery...")
        all_leads = []

        # 1. Reddit Scraping (Most reliable for homeowner requests)
        logger.info("📱 Scraping Reddit for homeowner requests...")
        reddit_leads = await self.social.scrape_reddit_posts(
            subreddits=["r/forhire", "r/Miami", "r/HomeImprovement"],
            keywords=["landscaping", "yard work", "lawn care"],
        )
        all_leads.extend(reddit_leads)
        logger.info(f"   Found {len(reddit_leads)} Reddit leads")

        # 2. Generate queries for Exa/Brave search (to be used via MCP tools)
        logger.info("🔍 Generating search queries for MCP discovery...")
        exa_queries = self.exa.generate_search_queries()
        brave_queries = self.brave.generate_dork_queries()

        # Save queries for MCP tool invocation
        queries_output = {
            "generated_at": datetime.now().isoformat(),
            "exa_queries": exa_queries[:20],  # Limit for token efficiency
            "brave_dork_queries": brave_queries[:20],
            "instructions": {
                "exa": "Use web_search_exa or deep_search_exa with these queries",
                "brave": "Use Brave Search MCP with these dork queries",
            },
        }

        queries_path = os.path.join(self.output_dir, "mcp_search_queries.json")
        with open(queries_path, "w") as f:
            json.dump(queries_output, f, indent=2)
        logger.info(
            f"   Saved {len(exa_queries) + len(brave_queries)} queries to {queries_path}"
        )

        # 3. Deduplicate leads
        seen_urls = set()
        unique_leads = []
        for lead in all_leads:
            if lead.source_url not in seen_urls:
                seen_urls.add(lead.source_url)
                unique_leads.append(lead)

        logger.info(f"✅ Discovery complete: {len(unique_leads)} unique leads")
        return unique_leads

    def save_leads(self, leads: list[Lead], filename_base: str = "mcp_leads"):
        """Save leads to JSON and CSV formats."""
        if not leads:
            logger.info("No leads to save")
            return

        lead_dicts = [lead.to_dict() for lead in leads]

        # JSON output
        json_path = os.path.join(self.output_dir, f"{filename_base}.json")
        with open(json_path, "w") as f:
            json.dump(lead_dicts, f, indent=2)

        # CSV output
        import pandas as pd  # type: ignore

        df = pd.DataFrame(lead_dicts)
        csv_path = os.path.join(self.output_dir, f"{filename_base}.csv")
        df.to_csv(csv_path, index=False)

        logger.info(f"💾 Saved {len(leads)} leads to {json_path} and {csv_path}")


# Example MCP query prompts for agent use
MCP_QUERY_EXAMPLES = """
## Exa MCP Query Examples for Lead Discovery

### Use web_search_exa for:
"site:reddit.com/r/forhire 'landscaping' 'miami' 'hiring'"
"site:twitter.com 'looking for landscaper' 'south florida' -filter:retweets"
"site:nextdoor.com 'broward' 'need' 'yard work'"

### Use deep_search_exa for comprehensive research:
"homeowners in Miami looking for landscaping services recommendations reddit"
"South Florida residents hiring for lawn care yard work"

### Use company_research_exa for competitor analysis:
Research landscaping companies in Broward County for service gap analysis

## Brave Search Dork Examples

### Reddit Discovery:
site:reddit.com/r/forhire "video editor" "hiring"
site:reddit.com "miami" "looking for" landscaper

### Twitter Discovery:
site:twitter.com "looking for graphic designer" -filter:retweets
site:x.com "need help with my yard" "florida"
"""


async def main():
    """Run the MCP-integrated lead discovery."""
    aggregator = MCPLeadAggregator()
    leads = await aggregator.run_discovery()
    aggregator.save_leads(leads)

    print("\n" + "=" * 60)
    print("MCP INTEGRATION READY")
    print("=" * 60)
    print(f"\n📊 Discovered {len(leads)} leads from browser automation")
    print(
        "📝 Search queries saved to: C:/Users/futur/gemini_workspace/mcp_search_queries.json"
    )
    print("\n🔧 Next Steps:")
    print("1. Use Exa MCP tools with generated queries for semantic search")
    print("2. Use Brave Search MCP for dork query discovery")
    print("3. Review mcp_search_queries.json for optimized queries")
    print("\n" + MCP_QUERY_EXAMPLES)


if __name__ == "__main__":
    asyncio.run(main())
