# Pedido de revisión independiente: bot de mercados de predicción cripto de 15 minutos (Kalshi)

Te pido un análisis crítico e independiente de esta estrategia. Busco especialmente **errores de razonamiento, sesgos en las pruebas, cosas que no estamos mirando e ideas nuevas**. Preferimos que nos digas que algo está mal a que nos confirmes lo que ya pensamos.

---

## 1. El mercado

- **Plataforma:** Kalshi (EE.UU., regulada por la CFTC). Contratos binarios que pagan $1 si se cumple el evento y $0 si no.
- **Mercados que operamos:** "¿la moneda va a estar arriba o abajo de su precio de apertura a los 15 minutos?". Abre un mercado nuevo cada 15 minutos, todo el día, para BTC, SOL, DOGE, XRP, NEAR y BNB (también hay ETH, HYPE y ZEC, que no usamos).
- **Objetivo (strike):** el precio del índice de Kalshi para esa moneda al abrir el mercado (CF Benchmarks / índice propio, publicado en vivo).
- **Se compra el SÍ o el NO** al precio de venta (ask) del libro. Los precios van de 1¢ a 99¢.
- **Comisión de Kalshi:** `ceil(0.07 × contratos × precio × (1 − precio))` en dólares, al comprar. No hay comisión al cobrar.
- **Liquidez:** BTC mueve unos 3 millones de contratos por mercado; ETH ~200 mil; XRP ~90 mil; DOGE ~45 mil; NEAR, BNB, HYPE y ZEC ~20 a 25 mil.

## 2. La estrategia actual (V10), en palabras

"Faltando entre 8 y 4 minutos para el cierre, si la moneda ya está bastante lejos de su objetivo, comprar el lado hacia donde está (el favorito), salvo que el contrato esté caro."

Reglas exactas:

1. **Ventana:** se mira solo cuando faltan entre 8 y 4 minutos para el cierre. El bot chequea cada 3 segundos y compra la primera vez que se cumplen las condiciones. Una sola compra normal por mercado.
2. **Distancia mínima** entre el precio actual del índice y el objetivo, proporcional a la volatilidad típica de cada moneda (≈ 4 movimientos típicos de 1 minuto × 0,75): BTC 0,094 %, SOL 0,188 %, DOGE 0,225 %, XRP 0,18 %, NEAR 0,398 %, BNB 0,083 %.
3. **Tope de precio:** no compra si el contrato cuesta más de 97¢.
4. **Horario bloqueado:** no opera mercados que cierran entre las 9:15 y las 12:00 (hora de Nueva York), por la apertura de la bolsa.
5. **Filtro de reversión:** no compra si en los 15 minutos ANTES de abrir el mercado la moneda ya se movió más de 2 "movimientos típicos de 15 minutos" hacia el lado que compraría (después de un envión fuerte, tiende a devolver).
6. **Filtro de precio justo (nuevo):** calcula P(termina arriba) = Φ( ln(precio/objetivo) / (σ·√minutos que faltan) ), con σ = movimiento típico de 1 minuto (1,4826 × mediana del |cambio logarítmico|) en la hora previa a la apertura. Si (probabilidad justa del lado − precio − comisión) < −3¢, no compra.
7. **Compra extra:** si después de comprar la moneda llega al doble de la distancia mínima a favor (y falta más de 2 minutos), compra otra vez el mismo monto. Hasta 99,5¢.
8. **Tamaño:** 3 % del saldo compartido por compra, mínimo $5, máximo $1.000.
9. **Sin stop-loss ni venta anticipada:** se espera el resultado.

Resultado típico: compra a ~89-93¢ y gana ~92-93 % de las veces. La ventaja estimada es de alrededor de 1 punto porcentual por encima de lo necesario para no perder.

## 3. Cómo llegamos acá (historia de versiones y lo que aprendimos)

- **V6:** distancia ×1, ventana 10-4, "en los últimos 2 minutos se alejó 1/10 de distancia", hasta 99¢, extra 50 %, 6 % del saldo. En el historial se vaciaba la cuenta en algunos meses.
- **V7:** igual que V6 con 3 % y sin operar de 9 a 12 h.
- **V8:** búsqueda sobre 12.960 combinaciones (buscando con dic-jun, comprobando con jul-oct): distancia ×0,75, ventana 8-4, sin filtro de tendencia, tope 97¢, extra 100 %.
- **V8.5:** V8 + filtro de reversión.
- **V9:** V8.5 + no operar mercados que empiezan en la hora en punto (:00) + 4,5 % en los que empiezan a :45 (en el historial, por minuto de inicio: :00 perdía, :45 ganaba en 11 de 11 meses).
- **V9.5:** V9 + ventana 8:30-3:30 + no comprar entre 7:30 y 5:30. En vivo perdió más que las demás.
- **V10:** V8.5 + filtro de precio justo. Es la que corre hoy con plata real.

## 4. Datos y método de prueba

- **Historial:** ~111.000 mercados (dic-2025 a oct-2026, las 5 monedas originales). Para cada mercado y cada minuto que falta (0-15): distancia de la moneda al objetivo (precio de Coinbase contra el objetivo de Kalshi) y bid/ask de Kalshi al cierre de cada vela de 1 minuto. Resultado oficial.
- **Validación:** buscamos con la primera mitad (dic-jun) y comprobamos con la segunda (jul-oct). Simulamos meses de 30 días con el saldo creciendo, tomando días reales en orden y también días al azar (2.000 meses), y medimos el mes típico, el mes malo (percentil 10), la probabilidad de caer debajo de cierto saldo y la caída máxima.
- **Comisión** calculada exacta (en una etapa la teníamos 100 veces más chica por un error, ya corregido).
- **Simulaciones en vivo:** en paralelo al bot real corren versiones simuladas con los mismos mercados en tiempo real (chequeando cada 6 segundos), con el mismo saldo inicial.

## 5. Resultados

**Historial (V10, 3 %, 30 días desde ~$325, días al azar):** mes típico ≈ ×3,5 el saldo, 2 % de meses terminan abajo, 13 % toca una caída a $250, caída típica 21 %.

**Hallazgos del historial:**
- El cálculo de precio justo está bien calibrado y muestra un **sesgo favorito-longshot**: los favoritos de 70-97 % ganan un poco más seguido de lo que dice su precio en Kalshi, y los contratos baratos ganan menos seguido. Esa sería la fuente de la ventaja.
- Comprar barato contra el precio justo (contratos de ~40¢) **pierde**; solo sirve como filtro para no comprar favoritos caros.
- Las compras caras (95-97¢) son las que menos ganan; las de 75-85¢ pierden más seguido pero dejan más por compra.
- Aflojar filtros (menos distancia, ventana más amplia, operar de 9 a 12, sacar la reversión) agrega compras que en promedio pierden.
- Frenos después de pérdidas o tras días malos, o pausas después de rachas ganadoras: **empeoran**. Después de pérdidas juntas, los cuartos de hora siguientes rinden más que lo normal.
- Días rojos y días verdes no se distinguen por nada observable antes (volatilidad previa, tendencia, resultado del día anterior).
- Por hora: de 9:30 a 10:30 (apertura de NY) es claramente malo. Otros "cuartos de hora malos" sueltos no se sostienen en una prueba walk-forward.
- Por moneda: BTC y ETH (las de más liquidez) son las que menos ventaja tienen; BNB, DOGE y XRP, las que más.
- En el S&P 500 por hora de Kalshi, en cambio, los favoritos ganan MENOS de lo que dice su precio (sin ventaja).

**En vivo (21 al 25 de octubre de 2026, ~450 compras reales, varias versiones):** el bot ganó 92,5 % de las compras cuando necesitaba 93,1 % para no perder: está más o menos en cero o un poco abajo, cuando el historial esperaba ~94 %. Varias pérdidas vinieron en bloque: las 3-5 monedas se dieron vuelta juntas en los últimos 2-3 minutos. Reconstruyendo las versiones sobre los mercados reales de esos días (minuto a minuto), ninguna gana de forma clara.

## 6. Lo que nos preocupa (por favor, critica esto)

1. **¿La ventaja del historial es real o es sobreajuste?** Probamos muchísimas variantes con los mismos 10 meses. ¿Cómo lo evaluarías?
2. **Precio de Coinbase contra índice de Kalshi:** el historial usa Coinbase y el bot usa el índice de Kalshi. En BNB, la diferencia al abrir es ~35 % de la distancia de compra. ¿Puede esto inflar la ventaja medida?
3. **Datos de 1 minuto:** la simulación ve un precio por minuto; el bot real compra en segundos y a veces paga 1-2¢ más. ¿Cuánto puede cambiar el resultado?
4. **¿Hay algo del futuro filtrándose** en alguna de las reglas (filtro de reversión, σ del precio justo, minuto de inicio)?
5. **¿Por qué en vivo rinde menos que en el historial?** ¿Mala racha normal con 450 compras, o un problema estructural (competencia, cambio en cómo Kalshi pone precios, tiempos)?
6. **Riesgo de correlación:** las 6 monedas se mueven juntas y a veces pierden todas en el mismo cuarto de hora. ¿Cómo dimensionarías la apuesta con eso en cuenta?

## 7. Lo que te pedimos

- Señalá **errores, sesgos o supuestos dudosos** en el método.
- Sugerí **variables, datos o filtros que no estemos mirando** (por ejemplo: libro de órdenes, futuros/perpetuos, liquidaciones, flujo de órdenes, volatilidad implícita, cómo calcula exactamente Kalshi el precio de cierre).
- Proponé **otras formas de ganar en estos mercados** (por ejemplo, poner órdenes límite en vez de comprar al ask).
- Decinos **cómo validarías esto** en vivo con el menor costo posible, y **con qué criterio subirías o bajarías el tamaño** de las apuestas.
- Si creés que la estrategia no tiene ventaja real, decilo y explicá por qué.

Gracias. Contestá en español, con detalle y priorizando lo que más impacto tendría.
