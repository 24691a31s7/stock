"""
Data Processing & Normalization layer.
Cleans and validates raw agent output before it reaches the analysis
layer: drops nulls/NaNs, converts historical records to a pandas
DataFrame, and flags data-quality issues as warnings instead of
crashing the pipeline.
"""
import pandas as pd


def historical_to_dataframe(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])

    df = pd.DataFrame(records)
    df["Date"] = pd.to_datetime(df["Date"], utc=True, errors="coerce")
    df = df.dropna(subset=["Date", "Close"])
    df = df.sort_values("Date").reset_index(drop=True)

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Close"])
    return df


def data_quality_warnings(collected: dict[str, dict]) -> list[str]:
    """Inspect the orchestrator's raw agent payload and produce
    human-readable warnings for anything that failed or came back empty."""
    warnings: list[str] = []
    for agent_name, payload in collected.items():
        if not payload.get("ok"):
            warnings.append(f"{agent_name} failed: {payload.get('error', 'unknown error')}")
        elif not payload.get("data"):
            warnings.append(f"{agent_name} returned no data")
    return warnings
