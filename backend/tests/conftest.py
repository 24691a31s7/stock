import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

# Make `app` importable when running `pytest` from the backend/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def synthetic_ohlcv_df() -> pd.DataFrame:
    """Deterministic synthetic OHLCV data (no network calls) used to unit
    test technical/pattern/risk logic in isolation."""
    rng = np.random.default_rng(42)
    n = 300
    dates = pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC")
    base = 100 + np.cumsum(rng.normal(0.05, 1.0, n))
    close = np.clip(base, 1, None)
    open_ = close + rng.normal(0, 0.5, n)
    high = np.maximum(open_, close) + abs(rng.normal(0, 0.3, n))
    low = np.minimum(open_, close) - abs(rng.normal(0, 0.3, n))
    volume = rng.integers(100_000, 2_000_000, n)

    return pd.DataFrame({
        "Date": dates, "Open": open_, "High": high, "Low": low,
        "Close": close, "Volume": volume,
    })


@pytest.fixture
def flat_ohlcv_df() -> pd.DataFrame:
    """A perfectly flat, low-volatility series — edge case for risk/technical agents."""
    n = 50
    dates = pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC")
    return pd.DataFrame({
        "Date": dates, "Open": [100.0] * n, "High": [100.5] * n,
        "Low": [99.5] * n, "Close": [100.0] * n, "Volume": [500_000] * n,
    })
