"""
BaseAgent: common contract for every agent in the system.

Design goals:
- Every agent exposes an async `run(ticker)` so the Orchestrator can
  fan them out with asyncio.gather() for true parallel execution.
- Blocking I/O (yfinance is synchronous under the hood) is pushed to a
  thread pool via `run_in_executor` so it doesn't block the event loop.
- Agents never raise: failures are caught and returned as a structured
  `{"ok": False, "error": ...}` payload so one flaky data source can't
  take down the whole pipeline. The Orchestrator/Risk layer treats a
  failed agent as missing data, not a fatal error.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger("alphaflow.agents")


class BaseAgent(ABC):
    name: str = "BaseAgent"

    @abstractmethod
    def collect(self, ticker: str) -> dict[str, Any]:
        """Synchronous, blocking implementation. Override this."""
        raise NotImplementedError

    async def run(self, ticker: str) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(None, self.collect, ticker)
            return {"agent": self.name, "ok": True, "data": result}
        except Exception as exc:  # noqa: BLE001 - agents must never crash the pipeline
            logger.warning("Agent %s failed for %s: %s", self.name, ticker, exc)
            return {"agent": self.name, "ok": False, "error": str(exc), "data": {}}
