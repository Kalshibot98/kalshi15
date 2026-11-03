"""Baja de Kalshi el valor oficial de liquidación de cada mercado operado en vivo, y de Coinbase las velas de 1 min."""
import csv, glob, json, os, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../datos/operaciones_reales")
def get(u):
    for i in range(5):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "research"}), timeout=30).read())
        except Exception as e:  # noqa
            time.sleep(1 + 2 * i); err = e
    raise err
filas = []
for f in glob.glob(H + "/*.csv"):
    m = os.path.basename(f).replace("operaciones", "").replace(".csv", "").strip("_") or "btc"
    for r in csv.DictReader(open(f)):
        r["moneda"] = m.upper(); filas.append(r)
tickers = sorted({r["mercado"] for r in filas})
def mercado(t):
    return t, get("https://api.elections.kalshi.com/trade-api/v2/markets/" + t)["market"]
mk = {}
with ThreadPoolExecutor(6) as ex:
    for t, m in ex.map(mercado, tickers): mk[t] = m
json.dump(mk, open("mercados.json", "w"))
print("mercados", len(mk))
# velas de 1 min de Coinbase por moneda alrededor de cada cierre
velas = {}
for mon in sorted({r["moneda"] for r in filas}):
    cierres = sorted({datetime.fromisoformat(mk[r["mercado"]]["close_time"].replace("Z", "+00:00")).timestamp()
                      for r in filas if r["moneda"] == mon})
    v = {}
    a, b = cierres[0] - 3600, cierres[-1] + 600
    s = a
    while s < b:
        e = min(s + 300 * 60, b)
        iso = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            for c in get(f"https://api.exchange.coinbase.com/products/{mon}-USD/candles?granularity=60&start={iso(s)}&end={iso(e)}"):
                v[int(c[0])] = c[4]   # cierre de la vela que empieza en c[0]
        except Exception as ex_:  # noqa
            print(mon, "sin velas", ex_); break
        s = e; time.sleep(0.15)
    velas[mon] = v; print(mon, len(v), "velas")
json.dump(velas, open("velas.json", "w"))
json.dump(filas, open("filas.json", "w"))
