"""Prueba de scrapling: diferencia entre el valor de liquidación de Kalshi (promedio de 60 s del índice CF)
y el precio spot (Coinbase) al cierre y al momento de decidir, por moneda, y cuántas compras dio vuelta."""
import json, statistics as st
from collections import defaultdict
from datetime import datetime
mk, velas, filas = (json.load(open(f)) for f in ("mercados.json", "velas.json", "filas.json"))
def spot(mon, ts):   # cierre de la vela de 1 min que termina en ts (o la anterior)
    v = velas[mon]; b = int(ts // 60 * 60) - 60
    for d in (0, -60, 60):
        if str(b + d) in v: return v[str(b + d)]
num = lambda x: float(str(x).replace("%", "").replace("+", ""))
R = defaultdict(lambda: defaultdict(list))
for r in filas:
    m = mk[r["mercado"]]
    if m.get("expiration_value") in (None, ""): continue
    mon, K, E = r["moneda"], float(m["floor_strike"]), float(m["expiration_value"])
    cierre = datetime.fromisoformat(m["close_time"].replace("Z", "+00:00")).timestamp()
    dec = cierre - num(r["minutos"].split()[0]) * 60
    C, Cd, P0 = spot(mon, cierre), spot(mon, dec), num(r.get("precio_moneda") or r["btc"])
    if C is None or Cd is None: continue
    s = 1 if r["lado"] == "SI" else -1
    gano = r["resultado"] == "ganó"
    x = R[mon]
    x["base_cierre"].append((E - C) / K * 1e4)                      # liquidación − spot al cierre (pb)
    x["base_decision"].append((P0 - Cd) / K * 1e4)                  # índice Kalshi − Coinbase al decidir (pb)
    x["dist_dec"].append(s * (P0 - K) / K * 1e4)                    # distancia a favor al decidir (pb)
    x["mov_contra"].append(s * (E - P0) / K * 1e4)                  # cuánto se movió a favor desde la decisión (pb)
    spot_gana = s * (C - K) > 0
    x["dio_vuelta_contra"].append(spot_gana and not gano)           # spot decía que ganábamos, la liquidación no
    x["dio_vuelta_favor"].append((not spot_gana) and gano)
    x["perdio"].append(not gano)
    x["ganancia"].append(num(r["ganancia"]))
print(f"{'mon':5}{'n':>5}{'perd%':>7}{'$':>9} | {'base cierre pb: media  desv':>28} | {'base decisión: media desv':>26} | {'dist decisión':>13} | vueltas contra/favor")
tot = defaultdict(list)
for mon, x in sorted(R.items()):
    n = len(x["perdio"])
    for k, v in x.items(): tot[k] += v
    print(f"{mon:5}{n:5}{100*sum(x['perdio'])/n:7.1f}{sum(x['ganancia']):9.2f} | {st.mean(x['base_cierre']):14.1f}{st.pstdev(x['base_cierre']):8.1f}      | "
          f"{st.mean(x['base_decision']):12.1f}{st.pstdev(x['base_decision']):8.1f}     | {st.median(x['dist_dec']):10.1f}    | "
          f"{sum(x['dio_vuelta_contra']):3} / {sum(x['dio_vuelta_favor']):3}")
x = tot; n = len(x["perdio"])
print(f"{'TOTAL':5}{n:5}{100*sum(x['perdio'])/n:7.1f}{sum(x['ganancia']):9.2f} | {st.mean(x['base_cierre']):14.1f}{st.pstdev(x['base_cierre']):8.1f}      | "
      f"{st.mean(x['base_decision']):12.1f}{st.pstdev(x['base_decision']):8.1f}     | {st.median(x['dist_dec']):10.1f}    | {sum(x['dio_vuelta_contra']):3} / {sum(x['dio_vuelta_favor']):3}")
# ¿las pérdidas fueron por la base o por movimiento real?
perd = [(c, f, m, d) for c, f, m, d, p in zip(x["base_cierre"], x["dio_vuelta_contra"], x["mov_contra"], x["dist_dec"], x["perdio"]) if p]
print(f"\nPérdidas: {len(perd)}. De esas, el spot al cierre todavía nos daba ganadores en {sum(1 for p in perd if p[1])}.")
print(f"Movimiento en contra desde la decisión en las pérdidas: mediana {st.median([-p[2] for p in perd]):.1f} pb, contra distancia a favor mediana {st.median([p[3] for p in perd]):.1f} pb")
json.dump({k: dict(v) for k, v in R.items()}, open("resultado.json", "w"))
