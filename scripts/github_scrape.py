"""
GitHub Actions Lead Scraper — ZERO API KEYS NEEDED
=====================================================
Runs inside GitHub Actions on a cron schedule.
1. Scrapes Craigslist for South Florida landscaping leads
2. Filters for genuine homeowner requests (not professional ads)
3. Writes results directly to docs/leads.json
4. GitHub Actions auto-commits the changes
5. GitHub Pages serves the updated dashboard — done!

No Supabase, no Firebase, no API keys. Just GitHub.
"""

import os
import json
import re
import asyncio
import logging
import random
from datetime import datetime
from typing import Optional

import requests  # type: ignore[import-untyped]
from bs4 import BeautifulSoup, Tag

# Try playwright (installed in CI), fall back to requests
try:
    from playwright.async_api import async_playwright  # type: ignore[import-not-found]

    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("GitHubScrape")

# ============================================================
# CONFIG — No secrets needed!
# ============================================================
CRAIGSLIST_BASE = "https://miami.craigslist.org"
CRAIGSLIST_REGIONS = ["", "/brw", "/pbc"]
CRAIGSLIST_CATEGORIES = ["lbg", "dom", "grd"]
SEARCH_QUERIES = [
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

EXTRA_BASES = [
    "https://orlando.craigslist.org",
    "https://daytona.craigslist.org",
    "https://treasure.craigslist.org",
]

# Professional ad signals to REJECT
PRO_FLAGS = [
    "licensed",
    "insured",
    "free estimate",
    "call us",
    "visit our",
    "website",
    "credit card",
    "finance",
    "satisfaction guaranteed",
    "we provide",
    "our company",
    "years of experience",
    "affordable rates",
    "our team",
    "family owned",
    "we install",
    "bonded",
    "dm for quote",
    "financing available",
    "accept credit cards",
]

SALES_FLAGS = ["for sale", "selling", "buy now", "discount", "limited time"]


# ============================================================
# SCRAPING
# ============================================================


async def fetch_page(url: str) -> Optional[str]:
    """Fetch page content. Uses Playwright if available, otherwise requests."""
    if HAS_PLAYWRIGHT:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                ctx = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/121.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1920, "height": 1080},
                )
                page = await ctx.new_page()
                await asyncio.sleep(random.uniform(0.5, 1.5))
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(random.uniform(1, 2))
                content = await page.content()
                await browser.close()
                return content
        except Exception as e:
            logger.warning(f"Playwright failed for {url}: {e}")

    # Fallback to requests
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.warning(f"Requests failed for {url}: {e}")
        return None


def score_lead(text: str) -> int:
    """Calculate homeowner intent score. Higher = more likely real homeowner."""
    score = 0

    # Personal pronouns (strong homeowner signal)
    personal = [
        r"\bi\b",
        r"\bmy\b",
        r"\bme\b",
        r"\bmy home\b",
        r"\bmy yard\b",
        r"\bour yard\b",
    ]
    if any(re.search(p, text) for p in personal):
        score += 25

    # Seeking help language
    help_pats = [
        r"\bneed\b",
        r"\blooking for\b",
        r"\bhire\b",
        r"\bhelp\b",
        r"\brecommend\b",
        r"\bwant\b",
    ]
    if any(re.search(p, text) for p in help_pats):
        score += 15

    # Specific project mentions
    project_kw = [
        "sod",
        "paver",
        "drainage",
        "irrigation",
        "hedge",
        "tree removal",
        "fence",
        "patio",
        "deck",
        "turf",
        "driveway",
    ]
    if any(kw in text for kw in project_kw):
        score += 10

    # Question patterns
    if "?" in text or any(
        p in text for p in ["anyone know", "can anyone", "does anyone"]
    ):
        score += 5

    # Location bonus
    fl_cities = [
        "miami",
        "broward",
        "fort lauderdale",
        "boca",
        "coral gables",
        "hollywood",
        "plantation",
        "weston",
        "davie",
    ]
    if any(c in text for c in fl_cities):
        score += 5

    return score


def parse_craigslist(html: str, base_url: str) -> list:
    """Parse Craigslist search results into lead dicts."""
    soup = BeautifulSoup(html, "html.parser")
    leads = []

    items = (
        soup.find_all("li", class_="cl-static-search-result")
        + soup.find_all("li", class_="result-row")
        + soup.select(".cl-results-list li")
    )
    if not items:
        items = soup.find_all("a", href=re.compile(r"/\d+\.html$"))

    for item in items:
        # Extract title element
        title_el: Optional[Tag] = None
        if isinstance(item, Tag) and item.name == "a":
            title_el = item
        elif isinstance(item, Tag):
            found = item.select_one(".titlestring") or item.find("a")
            if isinstance(found, Tag):
                title_el = found

        if title_el is None:
            continue

        title = title_el.get_text().strip()
        link = str(title_el.get("href", ""))
        if not link:
            continue
        if not link.startswith("http"):
            link = f"{base_url}{link}"

        full_text = ""
        if isinstance(item, Tag):
            full_text = item.get_text(separator=" ").lower()
        text = (full_text + " " + title.lower()).replace("\n", " ")

        # REJECT professional ads
        if any(f in text for f in PRO_FLAGS):
            continue

        # REJECT sales/spam
        if any(f in text for f in SALES_FLAGS):
            continue

        # Must show help-seeking or personal narrative
        intro_words = title.lower().split()[:2]
        needs_help = any(
            w in intro_words
            for w in ["need", "help", "looking", "want", "hire", "iso", "labor"]
        )
        resident_pats = [r"\bi\b", r"\bmy\b", r"\bme\b", r"\bneed\b", r"\bhelp\b"]
        is_narrative = any(re.search(p, text) for p in resident_pats)

        if not (is_narrative or needs_help):
            continue

        # Score and threshold
        sc = score_lead(text)
        if sc < 20:
            continue

        # Determine agency (location is derived from URL in the frontend)
        agency = "Verified Homeowner"
        if "/pbc/" in link:
            agency = "Palm Beach County"
        elif "/brw/" in link:
            agency = "Broward County"
        elif "/mdc/" in link:
            agency = "Miami-Dade"

        # Format for the EXISTING frontend (uses these exact key names)
        leads.append(
            {
                "Source_URL": link,
                "Job_Title": title[:200],
                "Agency": agency,
                "Closing_Date": "ASAP",
                "Score": sc,
                "Screened_At": datetime.utcnow().isoformat(),
            }
        )

    return leads


async def scrape_all() -> list:
    """Run the full scrape across all Craigslist regions."""
    logger.info("🌴 Scraping Craigslist South Florida + Central FL...")
    all_leads: list = []
    seen_urls: set = set()

    targets = []
    for base in [CRAIGSLIST_BASE] + EXTRA_BASES:
        regions = CRAIGSLIST_REGIONS if base == CRAIGSLIST_BASE else [""]
        for reg in regions:
            for cat in CRAIGSLIST_CATEGORIES:
                for query in SEARCH_QUERIES:
                    encoded_q = query.replace(" ", "+")
                    targets.append(
                        (base, f"{base}/search{reg}/{cat}?query={encoded_q}")
                    )

    random.shuffle(targets)
    targets = targets[:18]  # Limit per run to stay under CI time limits

    for base_url, url in targets:
        logger.info(f"   → {url}")
        html = await fetch_page(url)
        if html is None:
            continue

        leads = parse_craigslist(html, base_url)

        for lead in leads:
            if lead["Source_URL"] not in seen_urls:
                seen_urls.add(lead["Source_URL"])
                all_leads.append(lead)

        await asyncio.sleep(random.uniform(1.5, 3))

    logger.info(f"✅ Found {len(all_leads)} verified homeowner leads this run")
    return all_leads


# ============================================================
# LOCAL FILE OUTPUT — docs/leads.json
# ============================================================


def update_leads_json(new_leads: list) -> int:
    """Merge new leads into docs/leads.json, dedup by URL, keep last 200."""
    repo_root = os.getcwd()
    json_path = os.path.join(repo_root, "docs", "leads.json")

    # Load existing
    existing: list = []
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    # Merge: dedup by URL
    url_map: dict = {}
    for lead in existing:
        url = lead.get("Source_URL", "")
        if url:
            url_map[url] = lead

    # New leads override existing entries with same URL
    for lead in new_leads:
        url = lead.get("Source_URL", "")
        if url:
            url_map[url] = lead

    # Sort by Screened_At descending (newest first), keep top 200
    final = sorted(
        url_map.values(),
        key=lambda x: x.get("Screened_At", ""),
        reverse=True,
    )[:200]

    # Write
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w") as f:
        json.dump(list(final), f, indent=2)

    logger.info(f"📄 docs/leads.json updated: {len(final)} total leads")
    return len(final)


# ============================================================
# MAIN
# ============================================================


async def main() -> None:
    logger.info("=" * 60)
    logger.info("🌴 GITHUB ACTIONS LEAD SCRAPER — Zero API Keys")
    logger.info(f"   Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    logger.info(
        f"   Playwright: {'✅ Available' if HAS_PLAYWRIGHT else '⚠️ Using requests fallback'}"
    )
    logger.info("=" * 60)

    # Scrape
    leads = await scrape_all()

    if not leads:
        logger.info("No new leads found this run. Keeping existing data.")
        return

    # Update local file (GitHub Actions will commit & push this)
    total = update_leads_json(leads)

    logger.info("=" * 60)
    logger.info(f"✅ DONE — {len(leads)} new leads found, {total} total in database")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
