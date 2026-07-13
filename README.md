# AlphaFlow AI

**A Multi-Agent Intelligent Stock Market Analysis and Recommendation System**

AlphaFlow AI coordinates a team of specialized AI agents — data collection, technical/fundamental/sentiment analysis, prediction, risk assessment, recommendation, and explainability — behind a single orchestrator to produce transparent **Buy / Sell / Hold / Watchlist** calls for any publicly traded ticker.

> Live market and historical data is sourced via [`yfinance`](https://pypi.org/project/yfinance/) — free and keyless, so the whole system runs with **zero API keys** out of the box.

---

## Architecture

```
USER → Dashboard (React/HTML) → FastAPI → Orchestrator Agent
                                              │
        ┌─────────────────────────────────────┼─────────────────────────────────────┐
        ▼                                     ▼                                     ▼
 DATA COLLECTION LAYER              DATA PROCESSING LAYER                 ANALYSIS LAYER
 Market · Historical · News          Cleaning / Normalization      Technical · Fundamental
 Global Market · FII/DII                                           Sentiment · Pattern · Event
 Options · Company Fundamentals
        │                                                                    │
        └───────────────────────────► FEATURE ENGINEERING ◄─────────────────┘
                                              │
                          ┌───────────────────┼───────────────────┐
                          ▼                                       ▼
                 PREDICTION LAYER                          RISK LAYER
       Expected Return · Profit Probability      Volatility · Liquidity · Drawdown · Event
       Confidence Score · Price Direction
                          │                                       │
                          └───────────────► RECOMMENDATION LAYER ◄┘
                                          BUY / SELL / HOLD / WATCHLIST
                                                      │
                                                      ▼
                                         EXPLAINABLE AI (XAI) AGENT
                                        Human-readable "Why Buy/Sell?"
```

Full layer-by-layer breakdown is in the original `Abstract.txt` design doc; the code below implements every layer described there.

## Project layout

```
alphaflow-ai/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── orchestrator.py          # the "brain" — coordinates everything
│   │   │   ├── data_collection/         # Market, Historical, News, Global, FII/DII, Options, Company
│   │   │   ├── analysis/                # Technical, Fundamental, Sentiment, Pattern, Event
│   │   │   ├── prediction/              # Profit/Return/Confidence prediction
│   │   │   ├── risk/                    # Volatility, Liquidity, Drawdown, Event risk
│   │   │   ├── recommendation/          # Buy/Sell/Hold/Watchlist decision logic
│   │   │   └── explainability/          # XAI reasoning agent
│   │   ├── services/                    # data_processing.py, feature_engineering.py
│   │   ├── api/routes.py                # REST endpoints
│   │   ├── db/database.py               # SQLAlchemy models (Postgres/SQLite)
│   │   ├── cache/redis_cache.py         # Redis with in-memory fallback
│   │   ├── models/schemas.py            # Pydantic response contracts
│   │   ├── config.py                    # centralized settings & scoring weights
│   │   └── main.py                      # FastAPI app entrypoint
│   ├── tests/                           # 20 tests: unit (offline) + integration (live data)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── pytest.ini
├── frontend/static/index.html           # lightweight dashboard (no build step required)
├── .github/workflows/ci-cd.yml          # test → build → push → deploy pipeline
├── docker-compose.yml                   # backend + redis + postgres + frontend
└── README.md
```

## Quick start (local, no Docker)

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # optional — defaults work with zero config
uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000/docs** for interactive Swagger docs, or open `frontend/static/index.html` directly in a browser (it points at `http://localhost:8000/api/v1` by default).

Try it:
```bash
curl http://localhost:8000/api/v1/analyze/AAPL
curl http://localhost:8000/api/v1/analyze/SBIN.NS
curl http://localhost:8000/api/v1/history/AAPL
```

## Quick start (Docker Compose — full stack)

```bash
docker compose up --build
```
- Backend API → http://localhost:8000
- Dashboard → http://localhost:3000
- Redis → localhost:6379
- Postgres → localhost:5432

## Running tests

```bash
cd backend
pytest -m "not integration" -v   # 17 fast, fully offline unit tests
pytest -m integration -v         # 3 tests that call live yfinance + full API (needs internet)
pytest -v                        # everything
```

All 20 tests pass against this codebase as shipped.

## Configuration

All tunables live in `backend/app/config.py` / `.env` — nothing is hardcoded in agent logic:

| Variable | Purpose | Required? |
|---|---|---|
| `DATABASE_URL` | Postgres (prod) or SQLite (default, zero-setup) | No |
| `REDIS_URL` | Cache backend; falls back to in-memory automatically | No |
| `NEWSAPI_KEY` | Supplements yfinance news with NewsAPI.org | No |
| `FII_DII_API_KEY` | Enables institutional flow data via your licensed provider | No |
| `*_weight` | Feature Engineering scoring weights | No |

## Extending

- **Swap the prediction heuristic for a trained ML model:** `PredictionAgent.predict()` in `app/agents/prediction/prediction_agent.py` is the single seam — keep the same input/output shape and drop in a trained model (e.g. gradient boosting, LSTM).
- **Add a new data source agent:** subclass `BaseAgent`, implement `collect(ticker)`, register it in `OrchestratorAgent.__init__`.
- **Institutional (FII/DII) flow:** `FiiDiiAgent` is a pluggable adapter — wire in your licensed data vendor's client in `_fetch_from_provider`.

## Deploying to GitHub

```bash
git init
git add .
git commit -m "AlphaFlow AI: multi-agent stock analysis system"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

The included `.github/workflows/ci-cd.yml` will automatically:
1. Run the full test suite on every push/PR.
2. Build the backend Docker image and push it to `ghcr.io/<your-repo>/alphaflow-backend` on merges to `main`.
3. Provide ready-to-uncomment deploy steps for **Google Cloud Run** and **AWS EC2** (add the relevant secrets — `GCP_SA_KEY`, or `EC2_HOST`/`EC2_USER`/`EC2_SSH_KEY` — in your repo's Settings → Secrets → Actions).

## Disclaimer

AlphaFlow AI is a decision-support and educational tool. `PredictionAgent` uses a documented, transparent statistical heuristic — not a trained financial model — and no output should be treated as financial advice.
