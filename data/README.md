# Data

`raw/` holds the cached price files used by every run:

| File | Content | Source actually used |
|---|---|---|
| `raw/stocks_prices.csv` | Daily close, 12 NSE stocks, 2021-10-01 to 2026-09-25 | see `raw/stocks_source.json` |
| `raw/index_prices.csv`  | Daily close, NIFTY 50 index, 2015-01-01 to 2026-09-25 | see `raw/index_source.json` |

The cached files were downloaded from the public **eod2** NSE end-of-day dataset
(`github.com/BennyThadikaran/eod2_data`, files `daily/<symbol>.csv`). These prices are
adjusted for splits and bonuses, but **not** for dividends.

## Fallback order (`src/data_loader.py`)
1. **cache**: the CSVs in this folder (default; the demo runs offline)
2. **yfinance**: Yahoo Finance auto-adjusted close (`RELIANCE.NS`, ..., `^NSEI`)
3. **eod2**: the GitHub dataset above
4. **synthetic**: simulated prices. These are labelled `SYNTHETIC (simulated, not market data)`
   in the console, on every figure footer and in the results JSON, and are written to `outputs/synthetic/`.

To refresh: `python main.py --refresh-data` (skips the cache). To force one source:
`python main.py --source yfinance` (or `eod2`, `synthetic`, `cache`).

## Preprocessing decisions
- Keep only the configured window; drop dates where every series is missing (holidays).
- Forward-fill gaps of at most 3 trading days; **never back-fill** (that would leak future prices).
- Drop any remaining incomplete rows so all assets share one calendar.
- Use daily **log returns** r_t = ln(P_t / P_{t-1}). Part B uses them in percent.
