"""
NewsAgent — recent financial news headlines for a ticker.
Primary source: yfinance's bundled news feed (free, keyless).
If NEWSAPI_KEY is configured, results are supplemented with NewsAPI
for broader coverage — this is optional and the system works without it.
"""
import yfinance as yf
import httpx
from app.agents.base_agent import BaseAgent
from app.config import get_settings

settings = get_settings()


class NewsAgent(BaseAgent):
    name = "NewsAgent"

    def collect(self, ticker: str) -> dict:
        headlines: list[dict] = []

        tk = yf.Ticker(ticker)
        try:
            for item in (tk.news or [])[:10]:
                content = item.get("content", item)  # yfinance schema varies by version
                title = content.get("title") or item.get("title")
                publisher = (content.get("provider") or {}).get("displayName") if isinstance(
                    content.get("provider"), dict
                ) else item.get("publisher")
                if title:
                    headlines.append({"title": title, "publisher": publisher or "Unknown"})
        except Exception:
            pass  # yfinance news schema is not guaranteed stable; degrade gracefully

        if settings.newsapi_key and len(headlines) < 5:
            try:
                resp = httpx.get(
                    "https://newsapi.org/v2/everything",
                    params={"q": ticker, "sortBy": "publishedAt", "pageSize": 10,
                            "apiKey": settings.newsapi_key},
                    timeout=5.0,
                )
                if resp.status_code == 200:
                    for a in resp.json().get("articles", []):
                        headlines.append({"title": a["title"], "publisher": a["source"]["name"]})
            except Exception:
                pass

        return {"headlines": headlines, "count": len(headlines)}
