"""
EventAgent — flags proximity to known event risk (primarily upcoming
earnings dates, sourced from CompanyAgent). Feeds both the Feature
Engineering layer (event_score) and the Risk layer (event_risk_score).
"""
from datetime import datetime, timezone
import re


class EventAgent:
    name = "EventAgent"

    def analyze(self, next_earnings_date: str | None) -> dict:
        if not next_earnings_date:
            return {"event_score": 70.0, "days_to_earnings": None,
                     "note": "No known upcoming earnings date."}

        match = re.search(r"\d{4}-\d{2}-\d{2}", next_earnings_date)
        if not match:
            return {"event_score": 70.0, "days_to_earnings": None,
                     "note": "Could not parse earnings date."}

        try:
            earnings_dt = datetime.strptime(match.group(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days = (earnings_dt - datetime.now(timezone.utc)).days
        except ValueError:
            return {"event_score": 70.0, "days_to_earnings": None}

        # Closer to earnings => higher uncertainty => lower event_score
        # (event_score here represents "calmness", used positively in scoring)
        if days is None:
            score = 70.0
        elif days < 0:
            score = 70.0  # already reported, no imminent binary event
        elif days <= 3:
            score = 20.0
        elif days <= 7:
            score = 40.0
        elif days <= 14:
            score = 60.0
        else:
            score = 80.0

        return {"event_score": score, "days_to_earnings": days,
                "next_earnings_date": match.group()}
