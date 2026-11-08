**Update 12: what we tested on the second machine since last night, and the simulation that finally matches real money**

Update 11 only covered the Raspberry. Since last night we've also been running tests on a faster computer, because on 15-minute markets a second matters. Here is the rest.

**1. A simulation that finally matches real money**

We rebuilt the settlement index (CF Benchmarks BRTI) live from public exchange prices. Our copy usually differs from the official one by about 0.015%, and it agreed on the outcome in 366 of 392 closes. On top of that we ran a strategy for real, with 1 contract per trade, and a "twin" that simulates exactly the same decisions, side by side.

- Real, last night from 2 am to 11 am ET: 170 trades, 128 won, **−$8.70**. Most were quick sells for a small profit. The stop-losses (11 trades, −$6.60) ate the gains.
- On the 168 trades both ran: **real −$8.36, twin −$8.20**. They agreed on win or lose in 142 of 168 trades. On average the real fill price was 0.15¢ from the simulated one.
- The real bot also skipped 386 buys it wanted to make because the balance wasn't enough.

This is the first time our simulator's numbers were close to the real ones. Before, the paper version always looked better. From now on every simulation uses the real order book, the real queue ahead of us, and Kalshi's real fees. That lets us discard bad ideas before spending money.

**2. What we checked, and doesn't work** (30 days of 1-minute data, 9 coins, both halves of the month, counted per 15-minute window):

- betting against a 90%+ favorite;
- buying at 50¢ to sell at 55¢;
- following BTC (the other coins don't lag behind it);
- times of day and days of the week;
- streaks in one coin;
- 15-minute vs hourly markets (BTC, 701 hours: only 2 arbitrage chances, both under 1¢);
- a machine-learning model on 200,000 moments with 22 inputs, buying with a 1-minute delay: **it predicts worse than Kalshi's own price**.

Short version: **Kalshi prices these markets well.**

**3. Small patterns that keep showing up** (1–2 points, usable only with resting orders, which pay no taker fee):

- A favorite at 88–95% holds a bit more often than its price says.
- In "nervous" markets (3 or more lead changes), the favorite flips more. In calm ones, it holds more.
- With 2 minutes left, a 90%+ favorite flips more than its price implies: 6.7% vs 5.1%, mostly in HYPE, BNB and XRP.
- When all 4 coins flip, they tend to flip in the same window: 12 times vs 0.2 expected by chance.
- On combos, all 4 coins went the same way in 64.7% of windows. That's more on weekdays and when BTC is moving, less on weekends and in the New York afternoon.

**4. Settlement and speed** (first 38 minutes of data; we'll repeat it with many hours):

- Binance futures move about 1 second ahead of the BRTI. **But Kalshi's price moves in the same second as the futures**, so there's no time to exploit it from home.
- Settlement matched the average of the **last 60 real seconds**. We didn't see the 30-second lag discussed earlier in this thread. Thanks to whoever raised it: it was worth checking.

**5. Running now, in simulation, with real queue and real prices:**

- **Buy at a discount:** when the favorite costs 93–98¢ with 9–11 minutes left, leave resting orders 2–3¢ below, or at 85/80/70¢, and hold to the result. The backtest said +2 to +3.5%. With the real queue, the first 98 fills are close to zero (about −$1.80). We'll give it 1–2 days.
- **Combos at the open:** we ask Kalshi for a real $1 price on 4-coin and 3-coin combos (all up / all down), never accept, and simulate 10 strategies. It's too early for numbers.
- **Last minutes with futures:** we're still fixing how it sizes bets, so no numbers yet.

**The budget, again**

Testing has cost us about **$500 of our own money** so far. We still trade $1 at a time. Now we have a simulator that tracks the real results. We still need real money for the final check, though, and right now we can't even make every trade the strategy asks for.

Any contribution helps us keep testing until we find an edge or a pattern, or until we can say clearly that there isn't one. $5, $10, $20: the goal is $500 from everyone together. Received so far: $0.

USDC on Base: `0x5BF51DB5BD9F9E2E58cF97850495807E47388731`

We'll keep updating here. Repo: https://github.com/Kalshibot98/kalshi15
