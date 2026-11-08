**Update 11: everything we tested since Update 10, what's running live now, and why we need real money to keep going**

Short version: since Update 10 we tested seven new ideas with real money, at $1 each. Most of them lost. One small piece looks positive. A new idea is running in shadow mode right now. We'll keep posting every result here, good or bad.

**What we tested since Update 10 (real money, $1 per trade)**

| Test | Fills | Won | Avg price | Gap* | P&L |
|---|---|---|---|---|---|
| Early NO, 3-1 combos (14.8–12 min left) | 88 | 79 (90%) | 92.5¢ | −3 pts | −$3.16 |
| Early NO, 2-2 combos | 47 | 45 (96%) | 94.4¢ | +1 pt | +$0.50 |
| Early NO, 2-1 combos | 59 | 45 (76%) | 90.4¢ | −14 pts | −$9.61 |
| Late NO (YES at 70–90¢) | 21 | 5 (24%) | 26¢ | −2 pts | −$4.17 |
| Cheap YES, 1-1 / 2-1 only (last 6 min) | 10 | 6 (60%) | 26¢ | +34 pts | +$12.19 |
| Early YES on mixed combos (12–6.5 min) | 27 | 3 (11%) | 16¢ | −5 pts | −$6.18 |
| "Do the opposite": YES of the 2-1 combos at ~10¢ | 10 | 0 | 10¢ | −10 pts | −$10.00 |
| Copying big buyers ("whales", ≥ $100) on combos | 41 | 20 | — | — | −$7.06 |
| **Total** | **303** | | | | **−$27.49** |

*Gap = win rate minus average price paid. Positive means the price under-states the chance of winning, which is what an edge looks like. Fees are included in the P&L.

**What we learned**

- **The early NO does what our quote logger warned about.** It wins 90% of the time and still loses money, because it costs 92–94¢. The 2-2 version is the only one near zero (+$0.50).
- **The cheap YES on short combos is the only clearly positive piece:** +$12.19. But it's only 10 fills, so it could easily be luck. It keeps running, with its own ledger.
- **"Do the opposite" is the clearest lesson of the week.** Our history said the YES of those 2-1 combos at ~10¢ won 21–26% of the time. With real money it went 0 for 10. The simulation and the real market disagreed again.
- **Copying whales didn't carry over.** On the day we measured it, big YES buys on crypto combos won 88% while paying 62¢. When we copied them for real, our YES copies went 13 for 33 (−$7.83). The NO copies went 7 for 8 (+$0.77).
- On 7/11 the bot stopped itself with a safety check, when one buy didn't show up on the right side. It has been off since then, until we review it.

**Why the simulations kept fooling us.** Every time, the paper version looked better than the real one. Only last night did we learn to simulate in a more realistic way: using the prices and price requests that really existed at each moment, instead of assumed prices. So from now on we can screen ideas better before spending money. But the final check is still real money, because a simulation can't tell you if someone will actually take your trade at that price.

**What's running live now: being the one who quotes**

Until now we always asked for a price and accepted it, so we paid the quoter's margin. The new test flips that: we **answer** other people's price requests on 15-minute crypto combos. We offer to buy at our own model price minus 3¢. Before confirming, we check again with fresh prices. In a test, our model priced combos as well as the market did (Brier score 0.0773 vs 0.0777).

It's running in **shadow mode**: it records what it would offer, but doesn't send anything yet. So far it saw 13,546 requests on these markets that it could price. **Only 1,575 of them (12%) fit our $2 limit.** The median request would need about **$21** of risk. With $1–2 per trade, we can't even answer most of the market.

**The budget**

All of this is our own money. Counting every version since the first bot, testing has cost us about **$500**. We still bet $1 per trade because the budget is limited. We can't stop and only simulate, because the market behaves differently from the simulations, as "do the opposite" showed again this week.

The goal is still **$500 in total, from everyone together**. Any contribution helps: $5, $10 or $20 means more real tests, until we find an edge or a pattern that holds up, or until we can show clearly that there isn't one. Received so far: $0.

USDC on Base: `0x5BF51DB5BD9F9E2E58cF97850495807E47388731`

We'll keep updating this research here, with every result split by idea. Everything is in the repo: https://github.com/Kalshibot98/kalshi15
