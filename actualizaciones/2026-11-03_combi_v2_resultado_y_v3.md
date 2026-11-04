**Update 3: Combi V2 lost real money, and the real quotes point the opposite way**

As promised, the real results, good or bad.

**Combi V2 live (Nov 3):** it bought 6 combos, only when the real quote plus fee was *below* how often that price band won in our history. 3 won, 3 lost: **−$56.53**, balance from $92.11 to $35.57.

**What the quotes say.** The bot logged all 28 real combo quotes it got (11 to 24 market makers each), bought or not. We matched each one to how the combo actually settled:

| Real quote vs. our historical win rate | Quotes | Won | Avg price | P&L if we'd bought $20 each |
|---|---|---|---|---|
| **Cheaper** than history (what V2 bought) | 10 | 6 (60%) | 82¢ | −$58 |
| **Richer** than history (what V2 skipped) | 18 | 17 (94%) | 86¢ | +$30 |

So our "discount" was a warning sign. When market makers quoted a combo cheaper than our history implied, they were usually right. When they charged more than history implied, the combo held up. The quote seems to carry information our history doesn't: maybe recent volatility, maybe order flow.

**Next: V3 does the opposite.** Same signal (all four coins the same way, 6 to 3 minutes before close), but it buys only when the real quote is *richer* than our historical win rate, and skips the "bargains".

**The honest caveats:** 28 quotes from one day is very little, and the four losses came in one evening, so they are not independent. V3 could easily be wrong too. V3 will keep logging every quote it sees, bought or not, so the comparison above keeps growing for free, and we'll post it.

**Why we're asking for help.** Everything so far has come out of our own pocket: −$240 on the single-coin bot and −$56 on Combi V2. The paper results kept looking great, but they ran on prices that don't exist in real life. The only way we've found to learn anything is with real orders, and our own budget is nearly used up. We're willing to keep testing and refining versions in public, posting every trade. The goal is **$500 in total from everyone**, not from one person: $5, $10 or $20 helps.

USDC on Base only: 0x5BF51DB5BD9F9E2E58cF97850495807E47388731 · Repo: https://github.com/Kalshibot98/kalshi15
Not an investment, no returns promised. "No edge" is still a real possibility, and we'll publish it.
