# The math says memecoins are a gamble

A backtest of copying 4,293 Solana memecoin calls, a 100,000-trader Monte Carlo, and pumpdotfun's cumulative fees. This repo has the data snapshot, the scripts and the charts behind the X thread by [@KombuchoBuild](https://x.com/KombuchoBuild).

> **Not financial advice.** This is research on historical data under stated assumptions. It is not a recommendation to buy, sell or hold anything.

## Key findings

All 1h-vs-24h comparisons use the **same 4,186 calls** (Solana calls with both a 1h price and a 24h outcome). Returns are gross (no fees) unless stated.

### 1h (primary horizon)

| Metric | 1h | 24h (same calls) |
|---|---|---|
| Median return per copied call | **−12.6%** | −50.3% |
| Calls in the red | 60.9% | 75.7% |
| Calls up 10x or more | 0.6% (26 calls) | — |
| $100 on the typical (median) call becomes | $87 | $50 |
| Mean return, gross | **+16.5%** | +2.7% |
| Mean return after base costs (~7.24% round trip) | +8.1% | −4.8% |

- **The average is all tail.** Expected value E[R] = Σ p × r. Gross 1h EV buckets (share × average return = points): ≤−90%: −3.2 · −90 to −50%: −16.9 · −50 to 0%: −7.4 · 0 to +100%: +7.9 · 2x–10x: +19.0 · ≥10x: +17.1 → **sum +16.5**. Drop the 0.6% of calls that went 10x+ and the 1h EV is **−0.6%**.
- **Tail dependence.** Removing the best **24** of 4,186 calls (0.57%) makes the gross 1h mean negative. Without the top 1% (41 calls) it is −3.2%. The top 1% of calls produce 45% of all gains. After base costs, removing the best **6** calls makes the mean negative.
- **The edge is thin.** Get filled ≥8.1% worse than the market price at the call and the after-cost 1h mean is negative.
- **Most simulated traders lose.** 100,000 traders, $1,000 each, 10% of bankroll per call, 100 calls, base costs: **median ending bankroll $570**, mean $2,214, 32.7% end in profit, 45.5% lose half or more. At every bet size tested (2%–50%) fewer than half finish in profit.
- **The house always wins.** Traders paid **$2.23B** in fees on the pumpdotfun launchpad plus PumpSwap (to Oct 11, 2026); pumpdotfun kept **$1.32B** in revenue. With all positions closed, the sum of trader PnL in SOL equals −(fees + tips).

## Method and assumptions

- **Calls.** Karma's open dataset ([github.com/Kombucho/karma](https://github.com/Kombucho/karma), `validation/*.json`), snapshot Sep 16 – Oct 3, 2026. Filter: `status == "scored"`, Solana mints. 4,293 calls by 443 caller wallets have a 24h outcome; 4,186 of them also have a 1h price.
- **Returns.** Prices come from GeckoTerminal 15-minute candles, linearly interpolated within the candle. Entry = market price at the call timestamp (`market_price_at_entry`). 1h return = `price_1h / market_price_at_entry − 1`; 24h return = Karma's `copy_return_24h` (same formula).
- **Costs (per side, base).** pumpdotfun curve fee ~1.5% (DefiLlama fees ÷ volume, Sep 2026: 1.525%) + Axiom terminal fee 0.95% + 1% slippage (assumption) + 0.002 SOL priority/Jito per tx at SOL $120.07 on a $100 trade (assumption) = 3.69% per side, 7.24% round trip. A "cheap" scenario (2.24%/side) and a "+10% late entry" scenario are also reported.
- **Monte Carlo.** 100,000 traders, $1,000 start, fixed fraction of current bankroll per call, 100 calls, returns bootstrapped from the 4,186 real 1h returns, numpy seed `20261012`. "Ruin" = below $100 at any point.
- **Fees.** DefiLlama fees and volume API, daily series summed (pulled Oct 12, 2026, data to Oct 11, 2026 UTC).

## Limitations

- **15-minute candles.** Entry and exit are interpolated from 15-minute candles, so **1h is the shortest horizon tested**. Minute-level trades are not measured, and "take profit at 2x within 1h" cannot be computed (only a 24h peak is stored).
- **Entry at the market price at the call.** The backtest assumes you buy at the market price at the moment of the call. Real followers usually buy seconds to minutes later, into a spike, and pay more, which makes the backtest look better than reality. In one study a 30-second delay cut calls hitting +20% from 56.4% to 31.4%.
- **Leaderboard sample bias.** Callers were found via leaderboards, so the sample is not random. Calls are not independent (fewer distinct mints than calls).
- **Missing prices.** **47% of collected calls had no usable price data** and are excluded. Dead pools tend to drop out first, which likely flatters the results.
- **Cost assumptions.** Slippage, trade size and the late-entry premium are assumptions. Selling a 50x in a thin pool would move the price far more than 1%.

## Repository layout

```
data/
  karma_scored_calls.csv     all 5,668 scored calls (Solana + EVM) from the Karma snapshot:
                             wallet, handle, mint, chain, r24, peak, label, price_1h, market_price_at_entry
  results.json               24h analysis + DefiLlama fee totals (scripts/analysis.py)
  results_1h.json            1h analysis + Monte Carlo (scripts/analysis_1h.py)
  stats_1h_24h.json          1h vs 24h tables on the same calls (scripts/stats_1h_24h.py)
  pump_cumulative_fees.csv   daily cumulative pumpdotfun/PumpSwap fees and revenue
  defillama/                 raw DefiLlama fees/volume JSON
scripts/                     analysis code (karma_data.py = paths + CSV loader)
charts/                      the thread images
fonts/                       Geist and Inter (SIL OFL 1.1, licenses in fonts/OFL-*.txt)
```

`data/karma_scored_calls.csv` contains only public on-chain identifiers (caller wallets, public X handles as listed in the Karma dataset, token mints) and price fields.

## Reproduce

Python 3.11+ (tested with 3.13).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/analysis.py        # -> data/results.json
python scripts/analysis_1h.py     # -> data/results_1h.json, outputs/*.npy
python scripts/stats_1h_24h.py    # -> data/stats_1h_24h.json
python scripts/charts_shadcn.py   # -> charts/*.png
```

The run is deterministic (seeded) and regenerates `results.json`, `results_1h.json`, `stats_1h_24h.json` and the charts byte-for-byte: 1h median −12.6%, 1h mean +16.5%, Monte Carlo median ending bankroll $570. `charts/memecoin-contact-sheet.png` is a static preview and is not regenerated.

## Sources

- Karma dataset and method: [github.com/Kombucho/karma](https://github.com/Kombucho/karma); live API [karmawtf.vercel.app](https://karmawtf.vercel.app)
- GeckoTerminal (15-minute OHLCV candles, via Karma): [geckoterminal.com](https://www.geckoterminal.com)
- DefiLlama fees and volume API: [api.llama.fi/summary/fees/pump.fun](https://api.llama.fi/summary/fees/pump.fun?dataType=dailyFees), [/fees/pumpswap](https://api.llama.fi/summary/fees/pumpswap?dataType=dailyFees), [/fees/pump.fun-mobile-app](https://api.llama.fi/summary/fees/pump.fun-mobile-app?dataType=dailyFees), [/dexs/pump.fun](https://api.llama.fi/summary/dexs/pump.fun), [/dexs/pumpswap](https://api.llama.fi/summary/dexs/pumpswap)
- Axiom fees: [docs.axiom.trade/getting-started/fees/axiom-fees](https://docs.axiom.trade/getting-started/fees/axiom-fees) · priority/Jito defaults: [axiompedia.com/guides/fees](https://axiompedia.com/guides/fees)
- Lookonchain, pumpdotfun SOL sales: [lookonchain.com/feeds/75605](https://www.lookonchain.com/feeds/75605)
- Money Leaves Clues, "Inside the Economics of Pump.fun Call Channels": [moneyleavesclues.substack.com](https://moneyleavesclues.substack.com/p/inside-the-economics-of-pumpfun-call)

## License

Code: MIT (see `LICENSE`). Fonts keep their own SIL Open Font License. Third-party data stays under its sources' terms.

---

**Not financial advice.**
