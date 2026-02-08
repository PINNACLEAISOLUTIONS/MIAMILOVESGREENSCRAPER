# LandscapeLeadsFL - MCP-Enhanced Lead Generation

Multi-source lead discovery for landscaping services in South Florida, enhanced with Model Context Protocol (MCP) integrations for social media discovery.

## 🚀 Features

- **Traditional Scrapers**: Craigslist, Miami-Dade Government, Broward County, Google Search
- **MCP-Enhanced Discovery**: Exa Search, Brave Search, Reddit, TikTok
- **Smart Screening**: AI-powered homeowner intent detection (filters out professionals)
- **Cumulative Database**: Automatic deduplication and scoring

## 📋 Requirements

```bash
pip install -r requirements.txt
```

## 🔧 MCP Setup

### 1. Exa MCP (Recommended for Semantic Search)

Add to your MCP configuration (`settings.json` or `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "exa": {
      "type": "http",
      "url": "https://mcp.exa.ai/mcp?tools=web_search_exa,deep_search_exa,linkedin_search_exa",
      "headers": {}
    }
  }
}
```

Or with API key:
```json
{
  "mcpServers": {
    "exa": {
      "command": "npx",
      "args": ["-y", "exa-mcp-server", "tools=web_search_exa,deep_search_exa"],
      "env": {
        "EXA_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Get your API key at: https://dashboard.exa.ai/api-keys

### 2. Brave Search MCP (For Discovery Dorks)

```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your-brave-api-key"
      }
    }
  }
}
```

Get your API key at: https://brave.com/search/api/

### 3. Puppeteer/Playwright MCP (For Deep Scraping)

Already integrated via Patchright (patched Playwright) in `scrapers.py`.

## 🏃 Running the Pipeline

### Full MCP-Enhanced Mode (Recommended)
```bash
python main.py --mode full
```

### Legacy Mode (No MCP)
```bash
python main.py --mode legacy
```

### Generate MCP Queries Only
```bash
python main.py --mode queries
```

## 📁 Project Structure

```
LandscapeLeadsFL/
├── main.py              # Entry point with CLI
├── agents.py            # Scout, Screener, Formatter agents
├── scrapers.py          # Traditional web scrapers
├── mcp_integrations.py  # MCP-enhanced scrapers
├── requirements.txt     # Python dependencies
└── dashboard/           # Web dashboard for leads
```

## 🔍 MCP Query Examples

### Exa Semantic Search
```
"site:reddit.com 'miami' 'looking for' landscaper OR 'need landscaping'"
"homeowners in South Florida hiring for lawn care yard work"
```

### Brave Search Dorks
```
site:reddit.com/r/forhire "landscaping" "miami" hiring
site:twitter.com "looking for landscaper" "south florida" -filter:retweets
site:nextdoor.com "broward" "need" "yard work"
```

### Reddit API (via Reddit MCP)
- r/forhire
- r/HireAHelper
- r/Miami
- r/HomeImprovement
- r/landscaping

## 📊 Output

Leads are saved to:
- `C:/Users/futur/gemini_workspace/leads.json`
- `C:/Users/futur/gemini_workspace/leads.csv`
- `C:/Users/futur/gemini_workspace/mcp_search_queries.json`

## 🤖 Agent Prompt Examples

### For Exa MCP
```
"Use web_search_exa to find Reddit posts from Miami homeowners looking for landscaping services"
```

### For Brave Search MCP
```
"Use Brave Search with query: site:reddit.com/r/forhire 'landscaping' 'miami' 'hiring'"
```

### For Deep Research
```
"Use deep_search_exa to research South Florida landscaping demand and common homeowner pain points"
```

## ⚠️ Rate Limiting

- Reddit: 3-8 second delays between requests
- TikTok: 5-10 second delays (aggressive bot detection)
- Max 10 pages per session for browser automation

## 📝 Notes

- TikTok scraping is experimental due to aggressive anti-bot measures
- Use Brave Search dorks for discovery rather than direct scraping
- Exa semantic search provides better results than keyword matching
