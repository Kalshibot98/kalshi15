#!/usr/bin/env python3
"""Bot cripto 15 min para Kalshi (PRUEBA por defecto = reglas de la V10 con $5 fijos y corte en $250; también Justo / V9.5 / V9 / V8.5 / V8 / V7 con --version): BTC, SOL, DOGE, XRP y NEAR, todo en % del objetivo.
V8 (busqueda.py, 12.960 variantes; busca dic-jun, comprueba jul-oct): distancia ×0.75, ventana 8-4 min, sin filtro de
tendencia, no compra si el contrato vale más de 97¢, compra extra del 100%, 3% del saldo, no opera de 9 a 12 h.
V8.5 = V8 + no compra si en los 15 min ANTES de abrir el mercado la moneda ya se movió más de 2 "movimientos típicos"
de 15 min hacia el lado que compraría (después de un movimiento fuerte tiende a acomodarse; reversion.py).
V9 = V8.5 + no opera los mercados que EMPIEZAN en la hora en punto (:00-:15, pierden en el historial) y apuesta 4.5%
en los que empiezan a :45 (los mejores: ganan 11 de 11 meses). Resultado por minuto de inicio en rebote/cuartos.py.
V9.5 = V9 con ventana 8:30-3:30 y sin compras normales entre 7:30 y 5:30 (las que pasan la distancia recién ahí casi no
dejan ganancia; si sigue pasada, compra desde 5:30). rebote/ventanas_v9.py y minutos_v9.py.
Precio justo (rebote/precio_justo.py): P(SÍ) = Φ( ln(precio/objetivo) / (σ·√minutos que faltan) ), σ = movimiento típico
de 1 minuto del índice en la hora antes de abrir. V10 = V8.5 + no compra si justo − precio − comisión < −3¢.
"V10-3" = la V10 con el 3% de antes (simulada desde que la real pasó a 6%).
"Justo" = sin regla de distancia: compra el favorito (80-97¢) cuando está 2¢ o más barato que el precio justo.
V7: distancia ×1, ventana 10-4, filtro "se alejó 1/10 en 2 min", hasta 99¢, extra 50%, 3%, no opera de 9 a 12 h.
Un proceso por moneda; para sumar otra moneda alcanza con agregar un renglón en MONEDAS.

Regla (backtest 13/08-19/10/2026 en ~/kalshi-bots/rebote/proporcional.py):
  Faltando entre VENTANA_DESDE y VENTANA_HASTA minutos para el cierre, si la moneda (índice de Kalshi) está a
  la distancia mínima o más del precio objetivo, y en los últimos 2 minutos se alejó al menos 1/10 de esa distancia,
  comprar el lado hacia donde está la moneda y esperar el resultado. Sin stop, sin recompra.
  Una compra extra del 50% (V6) si llega al doble de la distancia a favor (≥1 min después, faltando >2 min).
Distancias en % del objetivo, proporcionales a cuánto se mueve cada moneda por minuto (≈4 movimientos típicos):
  BTC 0.125% (eran $100 con BTC a $80.000) · SOL 0.25% · DOGE 0.30% · XRP 0.24% · NEAR 0.53%. Si el precio cambia, se ajusta sola.
Todos los precios salen de Kalshi: el índice de cada moneda (el del gráfico de la app y el que fija el objetivo),
el de hace 2 minutos (historial propio del índice, o sus velas de 1 minuto al arrancar) y el libro de órdenes.
Apuesta (V7): 3% del saldo compartido, mínimo $5; no opera de 9 a 12 h (Florida); tope $1000 solo por liquidez (la orden IOC se llena
hasta donde alcance el libro dentro de 2¢ y el resto se cancela).

Uso:
  python3 bot_cripto.py --moneda SOL            (simulación de la V8: no usa clave ni manda órdenes)
  python3 bot_cripto.py --moneda SOL --version V7   (simulación de la V7, con sus propios archivos *_v7_*)
  python3 bot_cripto.py --moneda SOL --real     (plata real: requiere KALSHI_CONFIRMO_REAL=si)
Archivos por moneda: operaciones_sol.csv, estado_sol.json, estado_vivo_sol.json (bot_sol.log lo crea el arranque).
BTC usa los archivos de siempre (operaciones.csv, estado.json, estado_vivo.json, bot.log) para no perder el historial.
Freno: archivo STOP en esta carpeta -> ningún bot compra más.
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import math
import os
import random
import sys
import threading
import time
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from decimal import Decimal, ROUND_DOWN
from zoneinfo import ZoneInfo

# ----------------------------------------------------------------- parámetros
# reglas de cada versión (dist_mult multiplica la distancia base de cada moneda)
VERSIONES = {
    "PRUEBA": {"dist_mult": 0.75, "desde": 8, "hasta": 4, "tendencia": False, "tope_precio": 0.97, "extra": 0.0, "pct": 0.0,
               "reversion": 2.0, "justo_filtro": -0.03, "monto_fijo": 5.0, "corte": 250.0},   # prueba pública: reglas de la V10, $5 fijos por compra, frena si el saldo baja de $250
    "V10": {"dist_mult": 0.75, "desde": 8, "hasta": 4, "tendencia": False, "tope_precio": 0.97, "extra": 0.0, "pct": 0.06,
            "reversion": 2.0, "justo_filtro": -0.03},   # V8.5 + no compra lo que el precio justo marca caro (6% desde el 25/10; sin compra extra desde el 26/10: en vivo perdía)
    "V10-prom": {"dist_mult": 0.75, "desde": 8, "hasta": 4, "tendencia": False, "tope_precio": 0.97, "extra": 0.0, "pct": 0.06,
                 "reversion": 2.0, "justo_filtro": -0.03, "precio": "promedio"},   # la V10 de antes: decide con el promedio de 60 s
    "V10-3": {"dist_mult": 0.75, "desde": 8, "hasta": 4, "tendencia": False, "tope_precio": 0.97, "extra": 0.0, "pct": 0.03,
              "reversion": 2.0, "justo_filtro": -0.03},   # la misma V10 al 3% (simulada, para comparar con la real al 6%)
    "Justo": {"dist_mult": 0.75, "desde": 8, "hasta": 4, "tendencia": False, "tope_precio": 0.97, "extra": 0.0, "pct": 0.03,
              "solo_justo": {"margen": 0.02, "pmin": 0.80}},   # solo precio justo, sin distancia ni reversión ni extra
    "V9": {"dist_mult": 0.75, "desde": 8, "hasta": 4, "tendencia": False, "tope_precio": 0.97, "extra": 1.0, "pct": 0.03,
           "reversion": 2.0, "saltear_inicio": (0,), "pct_inicio": {45: 0.045},
           "continua": "V8.5"},   # la pantalla sigue sumando desde que arrancó la V8.5
    "V9.5": {"dist_mult": 0.75, "desde": 8.5, "hasta": 3.5, "tendencia": False, "tope_precio": 0.97, "extra": 1.0, "pct": 0.03,
             "reversion": 2.0, "saltear_inicio": (0,), "pct_inicio": {45: 0.045},
             "pausa": (5.5, 7.5),   # V9 con ventana 8:30-3:30 y sin comprar entre 7:30 y 5:30 (= minutos 7 y 6)
             "continua": "V9"},     # la pantalla sigue sumando desde que arrancó la V8.5
    "V8.5": {"dist_mult": 0.75, "desde": 8, "hasta": 4, "tendencia": False, "tope_precio": 0.97, "extra": 1.0, "pct": 0.03,
             "reversion": 2.0,   # no compra si antes de abrir ya se movió > 2 movimientos típicos de 15 min a favor
             },
    "V8": {"dist_mult": 0.75, "desde": 8, "hasta": 4, "tendencia": False, "tope_precio": 0.97, "extra": 1.0, "pct": 0.03},
    "V7": {"dist_mult": 1.0, "desde": 10, "hasta": 4, "tendencia": True, "tope_precio": 0.99, "extra": 0.5, "pct": 0.03},
}
VERSION_REAL = "PRUEBA"   # la que opera con plata real (usa los archivos de siempre)
APUESTA_MIN = 5.0         # mínimo $5 por compra (con 5 monedas a la vez, $10 era mucho riesgo con saldo chico)
ALEJO_SEG = 120
HORAS_SIN_OPERAR = {9, 10, 11}   # V7: no compra en mercados que cierran de 9:15 a 12:00 (Florida): abre NY, más pérdidas en bloque
EXTRA_HASTA_MIN = 2.0     # extra solo si faltan más de 2 minutos
EXTRA_ESPERA_SEG = 60     # extra al menos 1 minuto después de la compra normal
MARGEN_PRECIO = 0.02      # acepta pagar hasta 2¢ más que el mejor precio para que la orden se llene
SALDO_SIMULADO = 250.0
CADA_SEGUNDOS = 3

S3 = "https://kalshi-public-docs.s3.amazonaws.com/external/crypto/"
# dist en fracción del objetivo (0.0025 = 0.25%); "se alejó" = dist/10 y extra = 2×dist para todas las monedas.
MONEDAS = {
    "BTC":  {"serie": "KXBTC15M",  "fuente": S3 + "btc_history.json",  "dist": 0.00125, "mov15": 0.00139, "pct": 0.03, "tope": 1000.0,
             "archivos": ("operaciones.csv", "estado.json", "estado_vivo.json")},   # los de siempre (historial)
    "SOL":  {"serie": "KXSOL15M",  "fuente": S3 + "sol_history.json",  "dist": 0.0025,  "mov15": 0.00220, "pct": 0.03, "tope": 1000.0},
    "DOGE": {"serie": "KXDOGE15M", "fuente": S3 + "doge_history.json", "dist": 0.0030,  "mov15": 0.00212, "pct": 0.03, "tope": 1000.0},
    "XRP":  {"serie": "KXXRP15M",  "fuente": S3 + "xrp_history.json",  "dist": 0.0024,  "mov15": 0.00202, "pct": 0.03, "tope": 1000.0},
    "NEAR": {"serie": "KXNEAR15M", "fuente": S3 + "near_history.json", "dist": 0.0053,  "mov15": 0.00414, "pct": 0.03, "tope": 1000.0},
    # BNB (24/10): distancia y movimiento típico con la misma proporción que las otras (rebote/candidatas.py dias=400)
    "BNB":  {"serie": "KXBNB15M",  "fuente": S3 + "bnb_history.json",  "dist": 0.0011,  "mov15": 0.00143, "pct": 0.03, "tope": 1000.0},
}
# ----------------------------------------------------------------------------

API = "https://api.elections.kalshi.com/trade-api/v2"
SHARD = 2   # los mercados de cripto están en la parte (exchange_index) 2 de la cuenta
CARPETA = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_STOP = os.path.join(CARPETA, "STOP")
COMPARACION = os.path.join(CARPETA, "comparacion.json")   # {"desde", "saldo", "versiones": {V: {"desde", "saldo"}}}
ARG = ZoneInfo("America/New_York")   # hora de Florida
CAMPOS = ["hora", "modo", "mercado", "lado", "precio", "contratos", "costo", "comision",
          "precio_moneda", "objetivo", "distancia", "minutos", "resultado", "ganancia", "saldo_despues"]

# se completan en configurar()
MONEDA = SERIE = FUENTE = REGISTRO = ESTADO = VIVO = DECISIONES = ""
DIST = EXTRA = PCT = APUESTA_MAX = EXTRA_FRAC = PRECIO_TOPE = MOV15 = 0.0
REVERSION = None
PRECIO = "instante"          # "instante" = timeseries_adjusted (precio al instante); "promedio" = timeseries (promedio de 60 s, ~30 s atrasado)
MONTO_FIJO = None            # PRUEBA: dólares fijos por compra (en vez de % del saldo)
CORTE = None                 # PRUEBA: si el saldo baja de esto, crea el archivo STOP y no compra más
JUSTO_FILTRO = None          # V10: mínimo de (precio justo − precio − comisión) para comprar
SOLO_JUSTO = None            # "Justo": {"margen", "pmin"} compra solo por precio justo
PAUSA = None                 # (desde, hasta) en minutos que faltan: tramo de la ventana sin compras normales (V9.5)
SALTEAR_INICIO: tuple = ()   # minutos de inicio de mercado que no se operan (V9: en punto)
PCT_INICIO: dict = {}        # % de apuesta distinto según el minuto de inicio (V9: 4.5% a :45)
ALEJO = None
VENTANA_DESDE, VENTANA_HASTA = 8, 4
VERSION = VERSION_REAL
COMPARAR = False   # simulación de comparación: apuesta sobre un saldo compartido simulado (ver saldo_comparacion)


def configurar(moneda: str, version: str = VERSION_REAL) -> None:
    global MONEDA, SERIE, FUENTE, REGISTRO, ESTADO, VIVO, DECISIONES, DIST, ALEJO, EXTRA, PCT, APUESTA_MAX
    global PRECIO, VERSION, VENTANA_DESDE, VENTANA_HASTA, EXTRA_FRAC, PRECIO_TOPE, MOV15, REVERSION, SALTEAR_INICIO, PCT_INICIO, PAUSA, JUSTO_FILTRO, SOLO_JUSTO
    c, v = MONEDAS[moneda], VERSIONES[version]
    MONEDA, SERIE, FUENTE, VERSION = moneda, c["serie"], c["fuente"], version
    DIST = c["dist"] * v["dist_mult"]
    ALEJO = DIST / 10 if v["tendencia"] else None   # None = sin filtro de tendencia
    EXTRA = DIST * 2
    VENTANA_DESDE, VENTANA_HASTA = v["desde"], v["hasta"]
    EXTRA_FRAC, PRECIO_TOPE, PCT = v["extra"], v["tope_precio"], v["pct"]
    APUESTA_MAX = c["tope"]
    MOV15, REVERSION = c["mov15"], v.get("reversion")
    SALTEAR_INICIO, PCT_INICIO = v.get("saltear_inicio", ()), v.get("pct_inicio", {})
    PAUSA = v.get("pausa")
    JUSTO_FILTRO, SOLO_JUSTO = v.get("justo_filtro"), v.get("solo_justo")
    PRECIO = v.get("precio", "instante")
    global MONTO_FIJO, CORTE
    MONTO_FIJO, CORTE = v.get("monto_fijo"), v.get("corte")
    suf = moneda.lower()
    archivos = c.get("archivos") or (f"operaciones_{suf}.csv", f"estado_{suf}.json", f"estado_vivo_{suf}.json")
    if version != VERSION_REAL:   # la versión de comparación (simulada) lleva sus propios archivos
        v_ = version.lower()
        v_ = v_.replace(".", "")
        archivos = (f"operaciones_{v_}_{suf}.csv", f"estado_{v_}_{suf}.json", f"estado_vivo_{v_}_{suf}.json")
    REGISTRO, ESTADO, VIVO = (os.path.join(CARPETA, a) for a in archivos)
    DECISIONES = os.path.join(CARPETA, os.path.basename(REGISTRO).replace("operaciones", "decisiones"))


def pct(x: float, signo=True, dec=3) -> str:
    """Distancia al objetivo en % (la pantalla y los mensajes muestran las distancias en %; la plata, en dólares)."""
    return (("+" if x >= 0 else "-") if signo else "") + f"{100 * abs(x):.{dec}f}%"


def log(msg: str) -> None:
    print(f"{datetime.now(ARG):%d/%m %H:%M:%S}  {msg}", flush=True)


# ----------------------------------------------------------------- HTTP
def http(method: str, url: str, headers: dict | None = None, body: dict | None = None, timeout=10):
    data = json.dumps(body).encode() if body is not None else None
    h = {"User-Agent": "bot-cripto15", "Accept": "application/json"}
    if data is not None:
        h["Content-Type"] = "application/json"
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except Exception:  # noqa: BLE001
            return e.code, {}


class Firma:
    """Firma de pedidos autenticados de Kalshi (claves RSA o Ed25519)."""

    def __init__(self, key_id: str, ruta_clave: str):
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519, padding, rsa
        self._hashes, self._padding = hashes, padding
        self.key_id = key_id
        with open(ruta_clave, "rb") as f:
            self.clave = serialization.load_pem_private_key(f.read(), password=None)
        self.es_rsa = isinstance(self.clave, rsa.RSAPrivateKey)
        if not self.es_rsa and not isinstance(self.clave, ed25519.Ed25519PrivateKey):
            raise ValueError("La clave no es RSA ni Ed25519")

    def headers(self, method: str, path: str) -> dict:
        ts = str(int(time.time() * 1000))
        msg = (ts + method.upper() + path.split("?")[0]).encode()
        if self.es_rsa:
            sig = self.clave.sign(msg, self._padding.PSS(mgf=self._padding.MGF1(self._hashes.SHA256()),
                                                        salt_length=self._padding.PSS.DIGEST_LENGTH),
                                  self._hashes.SHA256())
        else:
            sig = self.clave.sign(msg)
        return {"KALSHI-ACCESS-KEY": self.key_id, "KALSHI-ACCESS-TIMESTAMP": ts,
                "KALSHI-ACCESS-SIGNATURE": base64.b64encode(sig).decode()}


class Kalshi:
    def __init__(self, firma: Firma | None):
        self.firma = firma

    def publico(self, path: str, **params):
        q = ("?" + urllib.parse.urlencode(params)) if params else ""
        return http("GET", API + path + q)

    def privado(self, method: str, path: str, body: dict | None = None):
        full = "/trade-api/v2" + path
        return http(method, API + path, headers=self.firma.headers(method, full), body=body)

    def mercado_abierto(self):
        st, d = self.publico("/markets", series_ticker=SERIE, status="open", limit=5)
        ms = d.get("markets", []) if st == 200 else []
        if not ms:
            # a veces Kalshi no devuelve el mercado con status=open (pasó el 20/10 15:00): buscarlo por horario
            ahora = time.time()
            st, d = self.publico("/markets", series_ticker=SERIE, min_close_ts=int(ahora), max_close_ts=int(ahora) + 1800, limit=10)
            if st != 200:
                return None
            ms = [m for m in d.get("markets", []) if m.get("status") in ("active", "open")
                  and datetime.fromisoformat(m["open_time"].replace("Z", "+00:00")).timestamp() <= ahora]
        ms = sorted(ms, key=lambda m: m["close_time"])
        return ms[0] if ms else None

    def mejor_precio_compra(self, ticker: str, lado: str):
        """Mejor precio para COMPRAR el lado, leído del libro de órdenes (al instante)."""
        st, d = self.publico(f"/markets/{ticker}/orderbook")
        if st != 200:
            return None
        ob = d.get("orderbook_fp") or d.get("orderbook") or {}
        def mejor(clave):
            ps = [float(x[0]) for x in (ob.get(f"{clave}_dollars") or []) if float(x[1]) > 0]
            return max(ps) if ps else None
        contra = mejor("no" if lado == "SI" else "yes")   # comprar SÍ = tomar a quien vende SÍ (= ofrece NO)
        return None if contra is None else round(1 - contra, 4)

    def resultado(self, ticker: str):
        st, d = self.publico(f"/markets/{ticker}")
        r = (d.get("market") or {}).get("result")
        return r if r in ("yes", "no") else None

    def saldo(self) -> float:
        """Saldo disponible en la parte de la cuenta donde están los mercados de cripto (SHARD).
        Es el mismo saldo que usa el bot de BTC."""
        for i in range(6):   # si Kalshi dice "demasiados pedidos" (429, p. ej. al arrancar los 5 bots juntos), reintentar
            st, d = self.privado("GET", f"/portfolio/balance?exchange_index={SHARD}")
            if st != 429:
                break
            time.sleep(2 ** i + random.random())
        if st != 200:
            raise RuntimeError(f"No pude leer el saldo ({st}): {d}")
        for b in d.get("balance_breakdown") or []:
            if int(b.get("exchange_index", -1)) == SHARD:
                return float(b.get("balance") or 0)
        return float(d.get("balance_dollars") or (d.get("balance", 0) / 100))

    def saldo_total(self) -> float:
        st, d = self.privado("GET", "/portfolio/balance")
        return float(d.get("balance_dollars") or 0) if st == 200 else 0.0

    def comprar(self, ticker: str, lado: str, precio: float, contratos: Decimal, grilla: list):
        """Compra inmediata (IOC). lado SI = bid de YES a `precio`; lado NO = ask de YES a 1-precio."""
        p_yes = precio if lado == "SI" else 1 - precio
        p_yes = redondear_grilla(p_yes, grilla, hacia_arriba=(lado == "SI"))
        body = {"ticker": ticker, "client_order_id": str(uuid.uuid4()),
                "side": "bid" if lado == "SI" else "ask",
                "count": f"{contratos:.2f}", "price": f"{p_yes:.4f}",
                "time_in_force": "immediate_or_cancel", "self_trade_prevention_type": "taker_at_cross"}
        st, d = self.privado("POST", "/portfolio/events/orders", body)
        if st not in (200, 201):
            if "insufficient_balance" in str(d):
                raise RuntimeError("Kalshi dice saldo insuficiente en la parte de cripto (shard 2)")
            raise RuntimeError(f"Orden rechazada ({st}): {d}")
        llenos = Decimal(str(d.get("fill_count") or "0"))
        prom = float(d.get("average_fill_price") or p_yes)
        prom_lado = prom if lado == "SI" else 1 - prom
        fee = float(d.get("average_fee_paid") or 0) * float(llenos)
        return llenos, prom_lado, fee, d


def redondear_grilla(p: float, grilla: list, hacia_arriba: bool) -> float:
    step = 0.01
    for r in grilla or []:
        if float(r["start"]) <= p <= float(r["end"]):
            step = float(r["step"]); break
    q = Decimal(str(step))
    v = (Decimal(str(p)) / q)
    v = (v.to_integral_value(rounding="ROUND_CEILING" if hacia_arriba else "ROUND_FLOOR")) * q
    return float(min(max(v, Decimal("0.001")), Decimal("0.999")))


def comision(contratos: float, precio: float) -> float:
    return math.ceil(0.07 * contratos * precio * (1 - precio) * 100 - 1e-9) / 100


FEED: dict = {}   # último archivo del índice leído (trae también las velas de 1 minuto)


def precio_moneda():
    """Precio del índice de Kalshi para la moneda. "timeseries" es el PROMEDIO de los últimos 60 s (con eso se fija el
    objetivo y se cobra, pero va ~30 s atrasado); "timeseries_adjusted" es el precio AL INSTANTE (25/10: desde ahora se
    decide con este, salvo la versión "promedio"). Si el dato tiene más de 30 segundos, devuelve None y el bot no compra."""
    st, d = http("GET", FUENTE, timeout=5)
    if st != 200 or not d.get("timeseries"):
        return None
    if time.time() - d.get("maturity_ts_ms", 0) / 1000 > 30:
        return None
    FEED.clear(); FEED.update(d)
    if PRECIO == "instante" and d.get("timeseries_adjusted"):
        return float(d["timeseries_adjusted"][-1])
    return float(d["timeseries"][-1])


def precio_en(t: float):
    """Precio del índice en el momento t (cierre de la vela de 1 minuto de Kalshi que termina más cerca; hay 2 h)."""
    velas = (FEED.get("candlesticks") or {}).get("1M") or []
    v = min(velas, key=lambda x: abs(x["open_ts_ms"] / 1000 + 60 - t), default=None)
    if v and abs(v["open_ts_ms"] / 1000 + 60 - t) <= 30:
        return float(v["close"])
    return None


def precio_hace(seg: float):
    """Precio del índice hace `seg` segundos, del cierre de la vela de 1 minuto de Kalshi que termina más cerca.
    Se usa recién arrancado, cuando el bot todavía no juntó 2 minutos de precios propios."""
    t = time.time() - seg
    velas = (FEED.get("candlesticks") or {}).get("1M") or []
    v = min(velas, key=lambda x: abs(x["open_ts_ms"] / 1000 + 60 - t), default=None)
    if v and abs(v["open_ts_ms"] / 1000 + 60 - t) <= 30:
        return float(v["close"])
    return None


def sigma_previa(apertura: float):
    """Movimiento típico de 1 minuto del índice (robusto: 1.4826 × mediana del |cambio|) en la hora antes de abrir."""
    velas = sorted((v["open_ts_ms"] / 1000 + 60, float(v["close"])) for v in (FEED.get("candlesticks") or {}).get("1M") or []
                   if apertura - 3600 < v["open_ts_ms"] / 1000 + 60 <= apertura)
    r = [abs(math.log(b[1] / a[1])) for a, b in zip(velas, velas[1:]) if a[1] > 0 and b[1] > 0]
    if len(r) < 30:
        return None
    r.sort()
    return 1.4826 * r[len(r) // 2] or None


def prob_si(px: float, obj: float, falt: float, sig: float) -> float:
    """Precio justo del SÍ: probabilidad de terminar arriba del objetivo (sin tendencia), con volatilidad sig por minuto."""
    z = math.log(px / obj) / (sig * math.sqrt(max(falt, 0.5)))
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


# ----------------------------------------------------------------- estado
class Estado:
    def __init__(self, modo: str):
        self.modo = modo
        self.lock = threading.Lock()
        self.saldo = SALDO_SIMULADO
        self.mensaje = "arrancando"
        self.ultimo_mercado = ""
        self.precio = None
        self.objetivo = None
        self.minutos = None
        self.operados: set[str] = set()
        self.rechazos: dict[str, int] = {}
        self.extras: set[str] = set()
        self.historial: list[tuple[float, float]] = []   # (hora, precio de la moneda)
        self.pendientes: dict[str, dict] = {}   # ticker -> operación esperando resultado
        self.ganancia_dia = 0.0
        self.dia = datetime.now(ARG).date()
        if os.path.exists(ESTADO):
            try:
                e = json.load(open(ESTADO))
                if e.get("modo") == modo:
                    self.saldo = e.get("saldo", self.saldo)
                    self.operados = set(e.get("operados", []))
                    self.pendientes = e.get("pendientes", {})
                    if e.get("dia") == str(self.dia):
                        self.ganancia_dia = e.get("ganancia_dia", 0.0)
            except Exception:  # noqa: BLE001
                pass

    def __setattr__(self, nombre, valor):
        if nombre == "saldo":   # anotar cuándo se leyó el saldo (la pantalla muestra el más nuevo de los bots)
            object.__setattr__(self, "saldo_ts", time.time())
        object.__setattr__(self, nombre, valor)

    def guardar(self):
        with self.lock:
            json.dump({"modo": self.modo, "saldo": self.saldo, "operados": sorted(self.operados)[-200:],
                       "pendientes": self.pendientes, "dia": str(self.dia),
                       "ganancia_dia": self.ganancia_dia}, open(ESTADO, "w"))


def anotar(fila: dict) -> None:
    nuevo = not os.path.exists(REGISTRO)
    with open(REGISTRO, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        if nuevo:
            w.writeheader()
        # las compras que dejó pendientes el bot.py viejo de BTC guardan el precio en "btc"
        w.writerow({k: fila.get(k, fila.get("btc", "") if k == "precio_moneda" else "") for k in CAMPOS})


CAMPOS_DEC = ["hora", "ts", "mercado", "decision", "lado", "minutos", "precio_moneda", "objetivo", "distancia",
              "yes_bid", "yes_ask", "precio_esperado", "precio_fresco", "precio_justo", "sigma", "z15",
              "apuesta", "contratos", "llenos", "precio_pagado", "comision"]


def anotar_decision(**d) -> None:
    """Registro de cada decisión final de un mercado (compra, extra o por qué se salteó), para analizar en vivo.
    Solo escribe: nunca cambia lo que hace el bot, y si falla no frena nada."""
    try:
        nuevo = not os.path.exists(DECISIONES)
        d.update(hora=f"{datetime.now(ARG):%d/%m %H:%M:%S}", ts=f"{time.time():.1f}")
        with open(DECISIONES, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CAMPOS_DEC, extrasaction="ignore")
            if nuevo:
                w.writeheader()
            w.writerow({k: (f"{v:.10g}" if isinstance(v, float) else v) for k, v in d.items() if v is not None})
    except Exception as e:  # noqa: BLE001
        log(f"no pude anotar la decisión: {e}")


def leer_registro() -> list[dict]:
    if not os.path.exists(REGISTRO):
        return []
    with open(REGISTRO) as f:
        return list(csv.DictReader(f))


# ----------------------------------------------------------------- lógica
def cerrar_pendientes(k: Kalshi, est: Estado, mercado_actual: str) -> None:
    for clave, op in list(est.pendientes.items()):
        ticker = op.get("mercado", clave)
        if ticker == mercado_actual:
            continue
        res = k.resultado(ticker)
        if not res:
            continue
        gana = (res == "yes") == (op["lado"] == "SI")
        cobro = float(op["contratos"]) * (1.0 if gana else 0.0)
        g = round(cobro - op["costo"] - op["comision"], 2)
        if est.modo == "SIMULACION":
            est.saldo += cobro
        else:
            try:
                est.saldo = k.saldo()
            except Exception as e:  # noqa: BLE001
                log(f"saldo: {e}")
        est.ganancia_dia += g
        op.update(resultado="ganó" if gana else "perdió", ganancia=f"{g:+.2f}", saldo_despues=f"{est.saldo:.2f}")
        anotar(op)
        del est.pendientes[clave]
        log(f"RESULTADO {clave}: {op['resultado']} {g:+.2f} USD · saldo ${est.saldo:.2f}")
        est.guardar()


def saldo_comparacion() -> float:
    """Saldo simulado compartido de una versión de comparación (como la cuenta real, uno solo para las 5 monedas):
    el saldo real al arrancar la comparación + lo que ya ganaron o perdieron sus 5 monedas."""
    tot = 0.0
    v_ = VERSION.lower().replace(".", "")
    for m in MONEDAS:
        ruta = os.path.join(CARPETA, f"operaciones_{v_}_{m.lower()}.csv")
        if os.path.exists(ruta):
            with open(ruta) as f:
                tot += sum(float(x["ganancia"] or 0) for x in csv.DictReader(f) if x["resultado"] in ("ganó", "perdió"))
    c = json.load(open(COMPARACION))
    return c.get("versiones", {}).get(VERSION, c)["saldo"] + tot


def ciclo(k: Kalshi, est: Estado) -> None:
    hoy = datetime.now(ARG).date()
    if hoy != est.dia:
        est.dia, est.ganancia_dia = hoy, 0.0
    m = k.mercado_abierto()
    if not m:
        est.mensaje = "no encontré mercado abierto"; return
    ticker = m["ticker"]; est.ultimo_mercado = ticker
    cerrar_pendientes(k, est, ticker)
    cierre = datetime.fromisoformat(m["close_time"].replace("Z", "+00:00")).timestamp()
    falt = (cierre - time.time()) / 60
    est.minutos = round(falt, 1)
    objetivo = m.get("floor_strike"); est.objetivo = objetivo
    px = precio_moneda(); est.precio = px
    ahora = time.time()
    if px:
        est.historial.append((ahora, px))
        est.historial = [x for x in est.historial if ahora - x[0] <= 600]
    if ticker in est.operados:
        intentar_extra(k, est, m, ticker, falt, px, objetivo); return
    if datetime.fromtimestamp(cierre - 1, ARG).hour in HORAS_SIN_OPERAR:
        est.mensaje = "horario sin operar (9 a 12 h: abre la bolsa de Nueva York)"; return
    inicio = datetime.fromtimestamp(cierre - 900, ARG).minute
    if inicio in SALTEAR_INICIO:
        est.mensaje = f"mercado que empieza a las :{inicio:02d}: no lo opero ({VERSION})"; return
    if not (VENTANA_HASTA <= falt <= VENTANA_DESDE):
        est.mensaje = f"fuera de la ventana ({VENTANA_DESDE} a {VENTANA_HASTA} min)"; return
    if PAUSA and PAUSA[0] < falt <= PAUSA[1]:
        est.mensaje = f"pausa entre {PAUSA[1]} y {PAUSA[0]} min: no compro (si sigue pasada, compro después)"; return
    if px is None or objetivo is None:
        est.mensaje = f"sin precio de {MONEDA} de Kalshi (o está atrasado) u objetivo: no compro"; return
    obj = float(objetivo)
    dist = (px - obj) / obj   # en fracción del objetivo
    lado = "SI" if dist > 0 else "NO"
    if SOLO_JUSTO:   # "Justo": compra el lado que Kalshi vende más barato que el precio justo (sin regla de distancia)
        sig = sigma_previa(cierre - 900)
        if not sig:
            est.mensaje = "sin volatilidad de la hora previa: no compro"; return
        p_si = prob_si(px, obj, falt, sig)
        yb, ya = float(m.get("yes_bid_dollars") or 0), float(m.get("yes_ask_dollars") or 0)
        v_si, v_no = p_si - ya - 0.07 * ya * (1 - ya), (1 - p_si) - (1 - yb) - 0.07 * yb * (1 - yb)
        if SOLO_JUSTO["pmin"] <= ya <= PRECIO_TOPE and v_si >= SOLO_JUSTO["margen"]:
            lado = "SI"
        elif SOLO_JUSTO["pmin"] <= 1 - yb <= PRECIO_TOPE and v_no >= SOLO_JUSTO["margen"]:
            lado = "NO"
        else:
            est.mensaje = (f"precio justo SÍ {p_si:.3f} (Kalshi {ya:.2f}/{1 - yb:.2f}): ningún favorito "
                           f"{100*SOLO_JUSTO['margen']:.0f}¢ más barato"); return
    elif abs(dist) < DIST:
        est.mensaje = f"{MONEDA} a {pct(dist)} del objetivo (< {pct(DIST, False)}): no opero"; return
    z = None
    if REVERSION is not None:   # V8.5: ¿la moneda ya venía disparada a favor en los 15 min antes de abrir?
        antes_abrir = precio_en(cierre - 1800)   # 15 min antes de la apertura (el objetivo es el precio al abrir)
        if antes_abrir:
            z = math.log(obj / antes_abrir) / MOV15 * (1 if dist > 0 else -1)
            if z > REVERSION:
                est.operados.add(ticker); est.guardar()
                anotar_decision(mercado=ticker, decision="reversion", lado=lado, minutos=falt, precio_moneda=px, objetivo=obj,
                                distancia=dist, yes_bid=m.get("yes_bid_dollars"), yes_ask=m.get("yes_ask_dollars"), z15=z)
                est.mensaje = (f"{MONEDA} ya venía disparada a favor antes de abrir ({z:.1f} movimientos típicos > "
                               f"{REVERSION:.0f}): salteo este mercado"); return
    if ALEJO is not None:   # filtro de tendencia (V7); la V8 no lo usa
        antes = [x for x in est.historial if ALEJO_SEG - 30 <= ahora - x[0] <= ALEJO_SEG + 30]
        if antes:
            px_antes = min(antes, key=lambda x: abs((ahora - x[0]) - ALEJO_SEG))[1]
        else:
            px_antes = precio_hace(ALEJO_SEG)   # recién arrancado: de las velas de 1 minuto de Kalshi
            if px_antes is None:
                est.mensaje = f"todavía no tengo el precio de {MONEDA} de hace 2 minutos: espero"; return
        alejo = abs(dist) - abs((px_antes - obj) / obj)
        if alejo < ALEJO:
            est.mensaje = (f"{MONEDA} a {pct(dist)}, pero en 2 min se alejó solo {pct(alejo, dec=4)} "
                           f"(< {pct(ALEJO, False, 4)}): espero"); return
    if os.path.exists(ARCHIVO_STOP):
        est.mensaje = "archivo STOP presente: no compro"; return

    yes_bid, yes_ask = float(m.get("yes_bid_dollars") or 0), float(m.get("yes_ask_dollars") or 0)
    precio = yes_ask if lado == "SI" else round(1 - yes_bid, 4)
    esperado, fresco = precio, None
    # real y simuladas: precio del libro al instante (el del listado de mercados llega atrasado; 25/10)
    fresco = k.mejor_precio_compra(ticker, lado)
    if fresco is not None:
        precio = fresco
    dec = dict(mercado=ticker, lado=lado, minutos=falt, precio_moneda=px, objetivo=obj, distancia=dist, yes_bid=yes_bid,
               yes_ask=yes_ask, precio_esperado=esperado, precio_fresco=fresco, z15=z)
    if SOLO_JUSTO:
        dec.update(precio_justo=p_si if lado == "SI" else 1 - p_si, sigma=sig)
    if precio > PRECIO_TOPE:
        est.operados.add(ticker); est.guardar()
        anotar_decision(decision="tope", **dec)
        est.mensaje = f"cumple la regla pero el contrato vale {precio:.3f} (> {PRECIO_TOPE:.2f}): salteo este mercado"; return
    if precio < 0.05:
        est.mensaje = f"precio raro ({precio}); no opero"; return
    if JUSTO_FILTRO is not None:   # V10: no comprar lo que el precio justo marca caro
        sig = sigma_previa(cierre - 900)
        if not sig:
            est.mensaje = "sin volatilidad de la hora previa para el precio justo: no compro"; return
        p_lado = prob_si(px, obj, falt, sig)
        p_lado = p_lado if lado == "SI" else 1 - p_lado
        ventaja = p_lado - precio - 0.07 * precio * (1 - precio)
        dec.update(precio_justo=p_lado, sigma=sig)
        if ventaja < JUSTO_FILTRO:
            est.operados.add(ticker); est.guardar()
            anotar_decision(decision="caro", **dec)
            est.mensaje = (f"precio justo {p_lado:.3f} contra {precio:.3f} ({100*ventaja:+.1f}¢ con comisión): "
                           f"caro, salteo este mercado"); return
    if est.modo == "REAL":
        est.saldo = k.saldo()
    elif COMPARAR:
        est.saldo = saldo_comparacion()
    if CORTE is not None and est.modo == "REAL" and est.saldo < CORTE:
        open(ARCHIVO_STOP, "w").write(f"saldo ${est.saldo:.2f} debajo del corte de ${CORTE:.0f}\n")
        est.mensaje = f"saldo ${est.saldo:.2f} debajo de ${CORTE:.0f}: fin de la prueba, creé el archivo STOP"; return
    apuesta = MONTO_FIJO or min(APUESTA_MAX, max(APUESTA_MIN, PCT_INICIO.get(inicio, PCT) * est.saldo))
    if apuesta > est.saldo:
        anotar_decision(decision="saldo", apuesta=apuesta, **dec)
        est.mensaje = "saldo insuficiente"; return
    contratos = (Decimal(str(apuesta)) / Decimal(str(precio))).quantize(Decimal("0.01"), rounding=ROUND_DOWN)

    if est.modo == "REAL":
        intentos = est.rechazos.get(ticker, 0)
        if intentos >= 3:
            est.operados.add(ticker); est.mensaje = "3 órdenes sin éxito en este mercado: lo salteo"; return
        est.rechazos[ticker] = intentos + 1
        limite = min(0.99, precio + MARGEN_PRECIO)
        llenos, p_real, fee, resp = k.comprar(ticker, lado, limite, contratos, m.get("price_ranges"))
        if llenos <= 0:
            anotar_decision(decision="sin_llenar", apuesta=apuesta, contratos=float(contratos), llenos=0, **dec)
            est.mensaje = f"orden sin llenar ({resp}); reintento en el próximo ciclo"; log(est.mensaje); return
        est.operados.add(ticker)   # anotar YA, antes de cualquier otra cosa que pueda fallar
        est.guardar()
        costo = float(llenos) * p_real
        try:
            est.saldo = k.saldo()
        except Exception as e:  # noqa: BLE001
            log(f"compré pero no pude leer el saldo: {e}")
    else:
        llenos, p_real = contratos, precio
        costo = float(llenos) * p_real
        fee = comision(float(llenos), p_real)
        est.saldo -= costo + fee

    est.operados.add(ticker)
    anotar_decision(decision="compra", apuesta=apuesta, contratos=float(contratos), llenos=float(llenos),
                    precio_pagado=p_real, comision=fee, **dec)
    op = {"hora": f"{datetime.now(ARG):%d/%m %H:%M}", "modo": est.modo, "mercado": ticker, "lado": lado,
          "precio": f"{p_real:.3f}", "contratos": f"{float(llenos):.2f}", "costo": round(costo, 2),
          "comision": round(fee, 2), "precio_moneda": f"{px:.6g}", "objetivo": objetivo, "distancia": pct(dist),
          "minutos": f"{falt:.1f}", "ts": time.time(), "apuesta": apuesta}
    est.pendientes[ticker] = op
    est.guardar()
    est.mensaje = f"COMPRÉ {lado} a {p_real:.3f} por ${costo:.2f}"
    log(f"{est.mensaje} · {ticker} · {MONEDA} {pct(dist)} · faltan {falt:.1f} min · saldo ${est.saldo:.2f}")


def intentar_extra(k: Kalshi, est: Estado, m: dict, ticker: str, falt: float, px, objetivo) -> None:
    """Una sola compra extra (EXTRA_FRAC de la normal) si la moneda llega a EXTRA (2× distancia) a favor."""
    if EXTRA_FRAC <= 0:
        est.mensaje = "este mercado ya lo operé (o lo salteé); espero el próximo (sin compra extra)"; return
    op = est.pendientes.get(ticker)
    clave = ticker + "#extra"
    if not op:
        est.mensaje = "este mercado ya lo operé (o lo salteé); espero el próximo"; return
    if clave in est.pendientes or ticker in est.extras:
        est.mensaje = "ya hice la compra normal y la extra; espero el próximo"; return
    if px is None or objetivo is None or falt <= EXTRA_HASTA_MIN:
        est.mensaje = "compra hecha; ya no hago extra en este mercado"; return
    obj = float(objetivo)
    a_favor = ((px - obj) if op["lado"] == "SI" else (obj - px)) / obj
    if time.time() - op.get("ts", 0) < EXTRA_ESPERA_SEG or a_favor < EXTRA:
        est.mensaje = (f"compra hecha; extra si llega a {pct(EXTRA, False)} a favor "
                       f"(está en {pct(a_favor)})"); return
    if os.path.exists(ARCHIVO_STOP):
        est.mensaje = "archivo STOP presente: no compro"; return
    lado = op["lado"]
    yes_bid, yes_ask = float(m.get("yes_bid_dollars") or 0), float(m.get("yes_ask_dollars") or 0)
    precio = yes_ask if lado == "SI" else round(1 - yes_bid, 4)
    esperado, fresco = precio, None
    # real y simuladas: precio del libro al instante (el del listado de mercados llega atrasado; 25/10)
    fresco = k.mejor_precio_compra(ticker, lado)
    if fresco is not None:
        precio = fresco
    if not (0.05 <= precio <= 0.995):
        est.mensaje = f"extra: precio raro ({precio}); no compro"; est.extras.add(ticker); return
    apuesta = EXTRA_FRAC * float(op.get("apuesta") or op["costo"])
    if est.modo == "REAL":
        est.saldo = k.saldo()
    if apuesta > est.saldo or apuesta < 0.5:
        est.mensaje = "extra: saldo insuficiente"; est.extras.add(ticker); return
    contratos = (Decimal(str(apuesta)) / Decimal(str(precio))).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    if est.modo == "REAL":
        intentos = est.rechazos.get(clave, 0)
        if intentos >= 3:
            est.extras.add(ticker); est.mensaje = "extra: 3 órdenes sin éxito, la salteo"; return
        est.rechazos[clave] = intentos + 1
        llenos, p_real, fee, resp = k.comprar(ticker, lado, min(0.995, precio + MARGEN_PRECIO), contratos, m.get("price_ranges"))
        if llenos <= 0:
            est.mensaje = f"extra: orden sin llenar ({resp})"; log(est.mensaje); return
        est.extras.add(ticker); est.guardar()
        costo = float(llenos) * p_real
        try:
            est.saldo = k.saldo()
        except Exception as e:  # noqa: BLE001
            log(f"compré extra pero no pude leer el saldo: {e}")
    else:
        llenos, p_real = contratos, precio
        costo = float(llenos) * p_real; fee = comision(float(llenos), p_real); est.saldo -= costo + fee
    est.extras.add(ticker)
    anotar_decision(mercado=ticker, decision="extra", lado=lado, minutos=falt, precio_moneda=px, objetivo=obj, distancia=a_favor,
                    yes_bid=yes_bid, yes_ask=yes_ask, precio_esperado=esperado, precio_fresco=fresco, apuesta=apuesta,
                    contratos=float(contratos), llenos=float(llenos), precio_pagado=p_real, comision=fee)
    op2 = {"hora": f"{datetime.now(ARG):%d/%m %H:%M}", "modo": est.modo, "mercado": ticker, "lado": lado,
           "precio": f"{p_real:.3f}", "contratos": f"{float(llenos):.2f}", "costo": round(costo, 2),
           "comision": round(fee, 2), "precio_moneda": f"{px:.6g}", "objetivo": objetivo, "distancia": pct(a_favor),
           "minutos": f"{falt:.1f} extra", "ts": time.time()}
    est.pendientes[clave] = op2
    est.guardar()
    est.mensaje = f"COMPRA EXTRA {lado} a {p_real:.3f} por ${costo:.2f}"
    log(f"{est.mensaje} · {ticker} · {MONEDA} {pct(a_favor)} a favor · faltan {falt:.1f} min · saldo ${est.saldo:.2f}")


def escribir_vivo(est: Estado) -> None:
    """Estado para la pantallita de la Raspberry."""
    try:
        json.dump({"moneda": MONEDA, "modo": est.modo, "saldo": est.saldo, "saldo_ts": est.saldo_ts, "hoy": est.ganancia_dia,
                   "frenado": os.path.exists(ARCHIVO_STOP), "mercado": est.ultimo_mercado, "precio": est.precio,
                   "objetivo": est.objetivo, "minutos": est.minutos, "mensaje": est.mensaje,
                   "pendientes": len(est.pendientes), "actualizado": time.time(),
                   "ventana": [VENTANA_DESDE, VENTANA_HASTA], "distancia_min": DIST, "version": VERSION}, open(VIVO + ".tmp", "w"))
        os.replace(VIVO + ".tmp", VIVO)
    except Exception:  # noqa: BLE001
        pass


def mostrar_estado(est: Estado) -> None:
    filas = [f for f in leer_registro() if f["modo"] == est.modo and f["resultado"] in ("ganó", "perdió")]
    gan = sum(1 for f in filas if f["resultado"] == "ganó")
    tot = sum(float(f["ganancia"] or 0) for f in filas)
    frenado = " FRENADO" if os.path.exists(ARCHIVO_STOP) else ""
    print(f"--- {MONEDA} {VERSION} {est.modo}{frenado} · saldo ${est.saldo:.2f} · hoy {est.ganancia_dia:+.2f} · "
          f"total {tot:+.2f} ({gan}/{len(filas)} ganadas)", flush=True)
    d = pct((est.precio - float(est.objetivo)) / float(est.objetivo)) if est.precio and est.objetivo else "-"
    print(f"    faltan {est.minutos} min · {MONEDA} vs objetivo {d} · {est.mensaje}", flush=True)


def main():
    ap = argparse.ArgumentParser(description="Bot cripto 15 min (simulación por defecto)")
    ap.add_argument("--moneda", required=True, choices=sorted(MONEDAS))
    ap.add_argument("--real", action="store_true", help="operar con plata real (requiere KALSHI_CONFIRMO_REAL=si)")
    ap.add_argument("--version", default=VERSION_REAL, choices=sorted(VERSIONES))
    ap.add_argument("--comparacion", action="store_true",
                    help="simulación para comparar con la real: arranca con el saldo de comparacion.json y lo comparte entre monedas")
    ap.add_argument("--cada", type=float, default=CADA_SEGUNDOS, help="segundos entre ciclos")
    a = ap.parse_args()
    if a.comparacion and a.real:
        sys.exit("--comparacion es solo para simulación.")
    if a.real and a.version != VERSION_REAL:
        sys.exit(f"Con plata real solo corre la {VERSION_REAL}; la {a.version} es solo para comparar en simulación.")
    configurar(a.moneda, a.version)
    global COMPARAR
    COMPARAR = a.comparacion
    firma = None
    modo = "SIMULACION"
    if a.real:
        if os.environ.get("KALSHI_CONFIRMO_REAL") != "si":
            sys.exit("Para operar con plata real exportá KALSHI_CONFIRMO_REAL=si (ver LEEME.md).")
        firma = Firma(os.environ["KALSHI_API_KEY_ID"], os.environ["KALSHI_PRIVATE_KEY_PATH"])
        modo = "REAL"
    k = Kalshi(firma)
    if a.version == VERSION_REAL:   # anotar desde cuándo corre esta versión (la pantalla cuenta desde ahí)
        ruta_v = os.path.join(CARPETA, "version_actual.json")
        try:
            actual = json.load(open(ruta_v))
        except Exception:  # noqa: BLE001
            actual = {}
        if actual.get("version") != VERSION:
            sigue = VERSIONES[VERSION].get("continua") == actual.get("version") and actual.get("desde")
            json.dump({"version": VERSION, "desde": actual["desde"] if sigue else time.time()}, open(ruta_v, "w"))
    est = Estado(modo)
    if modo == "REAL":
        est.saldo = k.saldo()
    elif COMPARAR:
        est.saldo = saldo_comparacion()
    tend = "sin filtro de tendencia" if ALEJO is None else f"se alejó {100*ALEJO:.4f}%"
    if REVERSION is not None:
        tend += f" · no compra si antes de abrir se movió > {REVERSION:.0f}×{100*MOV15:.3f}% a favor"
    log(f"{MONEDA} · {VERSION} · modo {modo} · saldo ${est.saldo:.2f} · ventana {VENTANA_DESDE}-{VENTANA_HASTA} min · "
        f"distancia {100*DIST:.4f}% del objetivo · {tend} · hasta {PRECIO_TOPE:.2f} · extra {EXTRA_FRAC:.0%} a {100*EXTRA:.3f}% · "
        f"apuesta {PCT:.0%}" + "".join(f" ({p:.1%} si empieza a :{m:02d})" for m, p in PCT_INICIO.items())
        + "".join(f" · no opera los que empiezan a :{m:02d}" for m in SALTEAR_INICIO)
        + (f" · pausa entre {PAUSA[1]} y {PAUSA[0]} min" if PAUSA else "")
        + (f" · no compra si precio justo − precio < {100*JUSTO_FILTRO:+.0f}¢" if JUSTO_FILTRO is not None else "")
        + f" · precio {'al instante' if PRECIO == 'instante' else 'promedio de 60 s'}"
        + (f" · SOLO PRECIO JUSTO: favoritos ≥{100*SOLO_JUSTO['pmin']:.0f}¢ con {100*SOLO_JUSTO['margen']:.0f}¢ de margen" if SOLO_JUSTO else "") + f" (${APUESTA_MIN:.0f}-${APUESTA_MAX:.0f})")
    ultimo_aviso = 0.0
    while True:
        try:
            ciclo(k, est)
            escribir_vivo(est)
            if time.time() - ultimo_aviso > 60:
                ultimo_aviso = time.time()
                mostrar_estado(est)
        except Exception as e:  # noqa: BLE001
            est.mensaje = f"error: {e}"
            log(est.mensaje)
            time.sleep(10)
        time.sleep(a.cada)


if __name__ == "__main__":
    main()
