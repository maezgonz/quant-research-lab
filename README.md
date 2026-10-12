# quant-research-lab

[![CI](https://github.com/maezgonz/quant-research-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/maezgonz/quant-research-lab/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> Quantitative finance research codebase: market data pipelines, derivatives pricing, portfolio optimization and algorithmic trading utilities — focused on Argentine markets (BYMA, ROFEX/MAE, CCL/MEP) and crypto.

Curated, sanitized extraction of my working research repository. All credentials load from environment variables — see [`.env.example`](.env.example).

## Packages

| Package | Contents |
|---|---|
| `src/data/` | Market data connectors: BCRA, BYMA, Rava, MAE, dólar blue, CCL, Alpha Vantage, Nasdaq Data Link, Google Sheets |
| `src/models/` | Black-Scholes, Monte Carlo (crypto portfolios), delta-gamma exposure, IV surface, LSTM price forecasting |
| `src/portfolio/` | Risk metrics, HRP / risk parity, carry trade, portfolio audit, data912 |
| `src/trading/` | Backtesting engine, market making, pairs arbitrage |
| `src/quant/` | RBF/GP price prediction with news sentiment, regime detection, signal research |
| `src/defi/` · `src/crypto/` | DeFi and crypto-specific analytics |
| `src/core/` | Centralized config (dotenv), constants |
| `src/utils/` | Retry logic, network helpers |

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # fill in your own API keys
```

All API keys are **optional per module** — modules degrade gracefully or raise a clear error if their key is missing.

## Highlights

- **HRP / risk-parity allocator** with real broker-data ingestion
- **Monte Carlo crypto portfolio engine** — simulation, clustering of efficient portfolios (silhouette-scored), rolling Sortino
- **RBF kernel + Gaussian Process forecaster** blended with RandomForest and news sentiment (NewsAPI)
- **Argentine-market data layer** — BCRA, BYMA, Rava, MAE, CCL/MEP dollar rates in one interface

## Notes

- Broker/live-trading connectors are **intentionally excluded** from this public repo.
- Historical market data files are not committed.
- See also: [quant-trading-models](https://github.com/maezgonz/quant-trading-models) (Monte Carlo & Greeks engines, C GBM kernel benchmarked on CESGA FinisTerrae-3).

## License

MIT — see [LICENSE](LICENSE).
