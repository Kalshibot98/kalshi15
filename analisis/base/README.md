# Settlement basis test (suggested by scraplingdata)

**Question:** does the gap between Kalshi's settlement value (a 60-second average of the CF Benchmarks index) and the spot price explain the live losses, especially BTC and XRP?

**Data:** the 989 live trades from Oct 19-28 that we could match (858 markets). Settlement value and strike come from Kalshi's API (`expiration_value`, `floor_strike`); spot comes from Coinbase 1-minute candles. "pb" = basis points of the strike.

| Coin | Trades | Lost | P&L | Basis at close (settlement − spot), mean ± sd | Kalshi index − Coinbase at decision | Median lead at decision | Flips against / for us |
|---|---|---|---|---|---|---|---|
| BNB | 137 | 7.3% | +$14.48 | +2.5 ± 4.1 pb | +2.6 ± 3.4 pb | 10.2 pb | 3 / 9 |
| BTC | 279 | 10.4% | −$139.71 | +0.3 ± 2.7 pb | +0.2 ± 3.0 pb | 13.0 pb | 2 / 4 |
| DOGE | 86 | 4.7% | −$7.85 | +2.5 ± 4.8 pb | +2.5 ± 5.1 pb | 27.4 pb | 2 / 0 |
| NEAR | 172 | 8.1% | −$31.65 | +5.1 ± 9.5 pb | +6.5 ± 8.4 pb | 50.1 pb | 1 / 6 |
| SOL | 124 | 4.8% | +$13.09 | +1.0 ± 3.4 pb | +1.3 ± 4.8 pb | 22.7 pb | 0 / 1 |
| XRP | 191 | 9.4% | −$77.67 | +1.9 ± 4.0 pb | +2.2 ± 4.4 pb | 23.0 pb | 2 / 5 |
| **Total** | **989** | **8.2%** | **−$229.31** | **+2.0 ± 5.4 pb** | **+2.4 ± 5.5 pb** | **22.0 pb** | **10 / 25** |

"Flip against" means spot at expiry said we won but settlement said we lost; "flip for" is the reverse.

## What it says
1. **The basis is real but small.** It averages about 2 pb, with a spread of about 5 pb, against a median lead of 22 pb when we bought. NEAR has the largest and noisiest basis, but it also has the largest lead.
2. **It helped more than it hurt.** It flipped 10 trades against us and 25 in our favor. It doesn't explain the losses.
3. **It doesn't explain BTC.** BTC has the smallest basis (0.3 ± 2.7 pb) and still lost the most money.
4. **The losses are real reversals.** Of the 81 losing trades, spot at expiry was still on our side in only 10. In the other 71, the price genuinely moved against us. The median move was 25 pb against, when we were a median of 19 pb ahead.

**Conclusion:** the settlement basis is not where the backtest edge went. The losses look like genuine late reversals, bigger and more frequent than a normal-distribution fair price expects. Our next test is a fat-tailed (Student-t) fair price.

Code: `bajar.py` (download) and `analizar.py` (analysis).
