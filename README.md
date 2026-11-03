# Kalshi 15-min crypto: open research

**[Español abajo](#español)**

Can Kalshi's 15-minute crypto markets ("will BTC/SOL/DOGE/XRP/NEAR/BNB finish above or below its opening price?") be beaten with a simple, rules-based bot? We're testing it in public, with real money, sharing every trade, including the losing ones.

## Status

| | |
|---|---|
| Backtest (Dec 2025 to Oct 2026, ~111k markets) | ~1 point of edge per trade (favorite-longshot bias) |
| Live, Oct 19-28 2026 (993 real trades, $11,937 traded) | **−$240 (−2% of volume)**. The latest versions were roughly flat |
| Combos (BTC+ETH+SOL+XRP), Nov 2026 | Real quotes run 2-10¢ above the product of the legs, so the paper run overstated the edge. Combi V2 tests live, small: buys only if quote + fee < historical win rate. See `actualizaciones/` |
| Next: public live test | 4 weeks, flat $5 per trade, stops if balance drops to $250. **Needs funding** |

## The strategy (V10 / PRUEBA)

With 8 to 4 minutes left, if the coin is already well away from its target, buy the favored side (~90-93¢), unless it's expensive versus a fair price computed from the last hour's volatility. Hold to settlement. Full rules, history of versions and open questions: [ESTUDIO.md](ESTUDIO.md) (Spanish).

## What's here

- `ESTUDIO.md`: the full study, written as a request for critical review.
- `datos/operaciones_reales/`: every real trade, Oct 19-28 (one CSV per coin; BTC is `operaciones.csv`).
- `codigo/bot_cripto.py`: the bot. `--version PRUEBA` (default) is the public-test config: V10 rules, flat $5, stop at $250. Runs in simulation unless you pass `--real`.
- `actualizaciones/`: weekly updates during the live test.

```bash
python3 codigo/bot_cripto.py --moneda BTC            # simulation, no key needed
```

## Support the test

**Goal: $500 in USDC on Base, in total, from everyone who wants to chip in.** No one is expected to send $500: $5, $10 or $20 all help, and the running total is posted in each update. It funds the live tests (the 4-week single-coin test and the small live combo test, Combi V2). **Not an investment, no returns promised.** "There's no edge" is a likely outcome, and it will be published too. If more than $500 arrives, trade size stays the same until there's a clear answer; the extra is reported and held for a second round.

USDC on **Base only**: `0x5BF51DB5BD9F9E2E58cF97850495807E47388731`

All incoming and outgoing transfers can be checked on-chain: [basescan.org/address/0x5BF5…8731](https://basescan.org/address/0x5BF51DB5BD9F9E2E58cF97850495807E47388731)

---

## Español

¿Se le puede ganar con un bot de reglas simples a los mercados cripto de 15 minutos de Kalshi? Lo estamos probando en público, con plata real, y compartimos cada operación, también las que pierden.

- **Historial (dic-2025 a oct-2026):** ~1 punto de ventaja por compra.
- **En vivo (19 al 28/10/2026):** 993 compras y −$240 (−2% de lo operado). Las últimas versiones quedaron prácticamente en cero.
- **Próximo paso:** 4 semanas en vivo con $5 fijos por compra. Si el saldo baja a $250, se frena. La meta es juntar **$500 en USDC (red Base) entre todos**: aportes de $5, $10 o $20 ya ayudan, y el total se publica en cada novedad.

**No es una inversión y no prometemos ganancias.** Todos los movimientos de la billetera se pueden verificar en la cadena.

Dirección (USDC, **solo red Base**): `0x5BF51DB5BD9F9E2E58cF97850495807E47388731`

Estudio completo: [ESTUDIO.md](ESTUDIO.md) · Operaciones reales: `datos/` · Código: `codigo/` · Novedades: `actualizaciones/`
