import asyncio
import random
import logging
import re
from patchright.async_api import async_playwright  # type: ignore
from bs4 import BeautifulSoup
from datetime import datetime

try:
    from googlesearch import search  # type: ignore
except ImportError:
    search = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScraper:
    async def get_page_content(self, url, use_stealth=True):
        """Ultra-stealthy page fetcher using Patchright (Patched Playwright)"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
            )
            page = await context.new_page()

            try:
                # Human behavior: Random wait before entry
                await asyncio.sleep(random.uniform(2, 5))
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)

                # Human jitter: Real users scroll and move mouse
                await page.mouse.move(
                    random.randint(100, 700), random.randint(100, 700)
                )
                await asyncio.sleep(random.uniform(1, 3))
                await page.evaluate(
                    "window.scrollTo(0, document.body.scrollHeight / 2)"
                )
                await asyncio.sleep(random.uniform(2, 4))

                content = await page.content()
                await browser.close()
                return content
            except Exception as e:
                logger.error(f"Anti-Ban: Failed to fetch {url} - {e}")
                await browser.close()
                return None


class CraigslistScraper(BaseScraper):
    def __init__(self):
        self.base_url = "https://miami.craigslist.org"
        self.regions = ["", "/brw", "/pbc"]
        # SHIFT: Focus on GIGS (Labor, Domestic) where homeowners ask for help.
        # Removed 'lbs' (Labor Services) and 'hss' (Household Services) as they are 99% vendor ads.
        self.categories = ["lbg", "dom", "grd"]
        self.search_queries = [
            "pavers",
            "sod",
            "landscaping",
            "landscaping needed",
            "tree removal",
            "tree cutting",
            "fill dirt",
            "artificial turf",
            "driveway",
            "patio",
            "hardscape",
            "re-sod",
        ]

    async def scrape(self):
        logger.info("Scout Agent: Hunting for Homeowner Gigs (Smart Read Mode)...")
        results = []
        seen_links = set()

        targets = []
        for reg in self.regions:
            for cat in self.categories:
                for query in self.search_queries:
                    encoded_q = query.replace(" ", "+")
                    targets.append(
                        f"{self.base_url}/search{reg}/{cat}?query={encoded_q}"
                    )

        random.shuffle(targets)
        for url in targets[:15]:
            content = await self.get_page_content(url)
            if not content:
                continue

            soup = BeautifulSoup(content, "html.parser")
            potential_items = (
                soup.find_all("li", class_="cl-static-search-result")
                + soup.find_all("li", class_="result-row")
                + soup.select(".cl-results-list li")
            )

            if not potential_items:
                potential_items = soup.find_all("a", href=re.compile(r"/\d+\.html$"))

            for item in potential_items:
                title_el = (
                    item
                    if item.name == "a"
                    else (item.select_one(".titlestring") or item.find("a"))
                )
                if not title_el:
                    continue

                title = title_el.get_text().strip()
                link = title_el.get("href", "")
                if not link or link in seen_links:
                    continue
                if not link.startswith("http"):
                    link = f"{self.base_url}{link}"

                text = (item.get_text(separator=" ").lower() + title.lower()).replace(
                    "\n", " "
                )

                # 1. READ THE ADS: Date Filtering (Last 30 Days)
                date_el = item.select_one(".result-date")
                if date_el and date_el.has_attr("datetime"):
                    post_date_str = date_el["datetime"]
                    try:
                        post_date = datetime.strptime(
                            post_date_str.split()[0], "%Y-%m-%d"
                        )
                        if (datetime.now() - post_date).days > 30:
                            continue  # Skip old posts
                    except ValueError:
                        pass  # If parsing fails, keep it (assume recent/bumped)

                # 2. READ THE ADS: Title Heuristics
                # Homeowners Ask (Need, Help, Looking). Pros Offer (Service, Installation, Free).
                intro_words = title.lower().split()[:2]
                needs_help = any(
                    w in intro_words
                    for w in ["need", "help", "looking", "want", "hire", "iso", "labor"]
                )
                is_offer = any(
                    w in intro_words
                    for w in [
                        "we",
                        "professional",
                        "top",
                        "best",
                        "affordable",
                        "quality",
                        "free",
                        "licensed",
                    ]
                )

                # 2. READ THE ADS: Narrative vs. Copy
                # Real people use 'I' and 'My'. Ads use 'We', 'Our', 'Call'.
                resident_pats = [
                    r"\bi\b",
                    r"\bmy\b",
                    r"\bme\b",
                    r"\bneed\b",
                    r"\bhelp\b",
                    r"\bour yard\b",
                    r"\bmy house\b",
                ]
                is_narrative = any(re.search(p, text) for p in resident_pats)

                # 3. REJECTION: Commercial Signals
                pro_flags = [
                    "licensed",
                    "insured",
                    "free estimate",
                    "call us",
                    "visit our",
                    "website",
                    "credit card",
                    "finance",
                    "satisfaction guaranteed",
                ]
                is_pro = any(f in text for f in pro_flags) or is_offer

                # Logic: Must NOT be Pro. Must be Narrative OR clearly asking for Help in title.
                if (is_narrative or needs_help) and not is_pro:
                    # Double check it's not a sale (common in Farm/Garden)
                    if "for sale" not in text and "selling" not in title.lower():
                        results.append(
                            {
                                "Source_URL": link,
                                "Job_Title": title,
                                "Agency": "Verified Homeowner",
                                "Closing_Date": "ASAP",
                                "Raw_Text": f"Request: {title}. Context: {text[:200]}",
                            }
                        )
                        seen_links.add(link)
                    seen_links.add(link)

        return results


class GoogleSearchNavigator(BaseScraper):
    async def scrape(self):
        if not search:
            return []
        logger.info("Scout Agent: Fishing for Homeowners on Social Forums...")
        leads = []
        queries = [
            'site:reddit.com "miami" "looking for" landscaper',
            'site:nextdoor.com "broward" "need" "landscaping"',
            'site:reddit.com "palm beach" "recommend" landscaper',
        ]
        for q in queries:
            try:
                links = list(search(q, num_results=3, sleep_interval=4))
                for link in links:
                    leads.append(
                        {
                            "Source_URL": link,
                            "Job_Title": f"Community Suggestion: {q[:30]}...",
                            "Agency": "Community Discovery",
                            "Closing_Date": "Ongoing",
                            "Raw_Text": f"Resident discussing landscaping needs on {q}",
                        }
                    )
            except Exception:
                pass
        return leads


class MiamiDadeScraper(BaseScraper):
    def __init__(self):
        self.url = "https://www.miamidade.gov/global/procurement/solicitations.page"

    async def scrape(self):
        logger.info("Scouting Government High-Value Projects...")
        content = await self.get_page_content(self.url)
        if not content:
            return []
        soup = BeautifulSoup(content, "html.parser")
        listings = []
        rows = soup.find_all("div", class_="solicitation-card") or soup.find_all("tr")
        for row in rows:
            text = row.get_text(separator=" ").strip()
            if any(
                k in text.lower() for k in ["landscaping", "irrigation", "paver", "sod"]
            ):
                title = row.find("h3") or row.find("a")
                listings.append(
                    {
                        "Source_URL": self.url,
                        "Job_Title": title.text.strip()
                        if title
                        else "Institutional Project",
                        "Agency": "Government Account",
                        "Closing_Date": "Refer to Portal",
                        "Raw_Text": text,
                    }
                )
        return listings


class BrowardScraper(BaseScraper):
    def __init__(self):
        self.url = "https://broward.bonfirehub.com/portal/?tab=openOpportunities"

    async def scrape(self):
        logger.info("Scouting Broward Institutional Bids...")
        content = await self.get_page_content(self.url)
        if not content:
            return []
        soup = BeautifulSoup(content, "html.parser")
        listings = []
        rows = soup.find_all("tr")
        for row in rows:
            text = row.get_text(separator=" ").strip()
            if any(k in text.lower() for k in ["landscaping", "irrigation"]):
                cols = row.find_all("td")
                if len(cols) > 2:
                    listings.append(
                        {
                            "Source_URL": self.url,
                            "Job_Title": cols[1].text.strip(),
                            "Agency": "Government Account",
                            "Closing_Date": cols[-1].text.strip(),
                            "Raw_Text": text,
                        }
                    )
        return listings
