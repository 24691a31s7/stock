"""
FiiDiiAgent — institutional (FII/DII) flow data.

There is no free, keyless, reliable public API for FII/DII flows.
This agent is built as a pluggable adapter:
  - If FII_DII_API_KEY is configured, it calls the configured provider.
  - Otherwise it returns a clearly-flagged neutral/unavailable payload
    (`source: "unavailable"`), so downstream layers do NOT silently
    treat missing institutional data as a bullish or bearish signal.

Replace `_fetch_from_provider` with your paid/licensed data vendor's
client when you have one (e.g. NSE bulk deals, a Bloomberg/Refinitiv
feed, or a scraped-and-licensed dataset).
"""
from app.agents.base_agent import BaseAgent
from app.config import get_settings

settings = get_settings()


class FiiDiiAgent(BaseAgent):
    name = "FiiDiiAgent"

    def collect(self, ticker: str) -> dict:
        if settings.fii_dii_api_key:
            return self._fetch_from_provider(ticker)

        return {
            "source": "unavailable",
            "fii_net_flow": None,
            "dii_net_flow": None,
            "note": "Set FII_DII_API_KEY to a licensed provider to enable this signal.",
        }

    def _fetch_from_provider(self, ticker: str) -> dict:
        # Placeholder integration point for a real institutional-flow vendor.
        # Kept intentionally unimplemented — wire up your provider's SDK here.
        raise NotImplementedError("Institutional flow provider not configured")
