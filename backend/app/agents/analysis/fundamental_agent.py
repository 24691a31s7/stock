"""
FundamentalAgent — converts raw company fundamentals (PE, EPS, ROE,
margins, leverage) into a 0-100 fundamental_score.
Heuristic thresholds are intentionally simple/transparent so they can
be swapped for a sector-relative model later.
"""
import numpy as np


class FundamentalAgent:
    name = "FundamentalAgent"

    def analyze(self, company: dict) -> dict:
        if not company:
            return {"fundamental_score": 50.0, "note": "No fundamental data available."}

        score = 50.0
        reasons = []

        pe = company.get("pe_ratio")
        if pe is not None:
            if 0 < pe < 20:
                score += 10; reasons.append("Attractive P/E ratio")
            elif pe > 50:
                score -= 10; reasons.append("High P/E ratio (expensive)")

        roe = company.get("roe")
        if roe is not None:
            if roe > 0.15:
                score += 12; reasons.append("Strong return on equity")
            elif roe < 0:
                score -= 12; reasons.append("Negative return on equity")

        margin = company.get("profit_margin")
        if margin is not None:
            if margin > 0.15:
                score += 8; reasons.append("Healthy profit margins")
            elif margin < 0:
                score -= 8; reasons.append("Negative profit margins")

        dte = company.get("debt_to_equity")
        if dte is not None:
            if dte < 50:
                score += 5; reasons.append("Low leverage")
            elif dte > 150:
                score -= 10; reasons.append("High leverage")

        eps = company.get("eps")
        if eps is not None and eps < 0:
            score -= 10
            reasons.append("Negative EPS")

        score = float(np.clip(score, 0, 100))
        return {"fundamental_score": round(score, 2), "reasons": reasons}
