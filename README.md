# IBEX Intraday Decision Engine — V1

Assistent de decisió intradia per IBEX35. **No és un bot**: no prediu res abans de l'obertura, només analitza la situació real en el moment exacte en què l'executes (09:45, 11:30, 16:00...).

## Estructura del projecte

```
config.py             -> Constants i pesos (l'únic lloc amb "números màgics")
models.py              -> Dataclasses compartides (PriceSnapshot, ScoreBreakdown, StockReport...)
data_loader.py          -> Descàrrega de dades via yfinance (preu, volum, index)
volume.py               -> Volum relatiu + score (0-100)
relative_strength.py    -> Força relativa vs IBEX + score
news.py                 -> Notícies via Google News RSS (gratuït) + classificació
energy.py               -> Energia del moviment (continua / s'esgota) + score
scoring.py              -> Score final ponderat + recomanació (COMPRAR/VIGILAR/EVITAR)
report.py               -> Explicacions i informe final (mobile-friendly)
main.py                 -> Orquestrador: run() executa tot el pipeline
IBEX_Intraday_Engine.ipynb -> Notebook de Colab llest per fer servir
```

## Ús a Google Colab

1. Puja els 9 fitxers `.py` a la carpeta de l'entorn de Colab (o al teu Drive).
2. Obre `IBEX_Intraday_Engine.ipynb`, executa la cel·la d'instal·lació.
3. Executa:
   ```python
   from main import run_multi_market
   run_multi_market()          # analitza IBEX35 + NASDAQ alhora (config.MARKETS_TO_RUN)
   ```
   O si nomes vols un mercat concret:
   ```python
   from main import run
   run(market="NASDAQ")        # o market="IBEX35"
   ```
4. Torna a executar la cel·la cada vegada que vulguis una foto nova de la sessió (09:45, 11:30, 16:00...).

### Projeccio de nivells de Fibonacci (`fibonacci.py`)

Cada accio de l'informe inclou ara els nivells de Fibonacci calculats sobre el rang de preu d'avui (maxim/minim):

- **Retrocessos** (23.6% / 38.2% / 50% / 61.8% / 78.6%): possibles zones on el preu podria "descansar" abans de continuar el moviment — es a dir, possibles nivells d'entrada.
- **Extensions** (127.2% / 161.8% / 200%): possibles objectius de sortida si el moviment continua mes enlla del rang actual.
- **Zona d'entrada suggerida**: la banda entre el 50% i el 61.8%, que es la mes vigilada pels traders tecnics.

La direccio (ALCISTA/BAIXISTA) es determina segons si el preu esta mes a prop del maxim o del minim del dia. Com sempre, aixo es una tecnica estandard d'analisi tecnica basada en proporcions matematiques, NO una prediccio — els nivells son referencies, no garanties.

### Filtres de qualitat afegits

**Notícies "roundup" (falsos positius):** articles generics del tipus "ofertes del 4 de juliol: descomptes fins al 60% de Hanes, Ninja, Apple, Shark..." ja NO es classifiquen com a notícia rellevant de l'empresa, encara que continguin paraules clau com "deal". El filtre (`config.NEWS_ROUNDUP_BLOCKLIST`) descarta titulars amb frases promocionals genèriques ("% off", "deals up to", "black friday"...) o amb massa marques en llista (3+ comes).

**Avís de moviment extrem:** quan una acció ja s'ha mogut molt avui (per defecte, ±4% o mes — configurable a `config.EXTREME_MOVE_WARNING_PCT`), s'afegeix un avís explícit de risc de correcció tècnica als propers dies, independentment de si el score diu COMPRAR. No canvia la recomanació ni prediu res, només avisa de no perseguir cegament un moviment ja molt gran.

### Punt d'entrada (`entry_signal.py`)

A partir d'ara, cada accio de l'informe inclou tambe una linia de **"Punt d'entrada"** que et diu si el moment actual es un bon punt per entrar-hi, no nomes si l'accio esta "forta":

- **RUPTURA**: preu a prop del maxim del dia amb energia accelerant. Pot ser un bon punt d'entrada si ve acompanyat de volum alt.
- **MARGE_RECORREGUT**: preu ja per sobre del VWAP pero encara lluny del maxim del dia — encara hi ha recorregut abans de topar amb el sostre d'avui.
- **SOBREESTES**: preu molt allunyat del VWAP i/o a prop del maxim amb l'energia esgotant-se. Entrar aqui vol dir pagar car i sense impuls fresc.
- **LATERAL**: sense senyal clar en cap sentit.

Tambe es mostra la distancia del preu al VWAP (preu mitja ponderat per volum del dia) i al maxim/minim del dia, mes una **referencia de risc** (VWAP o minim del dia) — no es un consell, nomes un nivell objectiu per situar-te.

Quan fas servir `compare.py` per comparar dues fotos, la taula tambe mostra si la qualitat d'entrada ha canviat entre les dues captures (p.ex. de MARGE_RECORREGUT a SOBREESTES vol dir que ja has perdut el millor moment).

**Important**: aixo no prediu res ni es un consell d'inversio. Nomes descriu, amb dades objectives (VWAP i rang del dia), la posicio del preu en aquest instant.

### Detectar lateral erratic / whipsaw (`regime.py`)

Per casos com Grifols, on l'accio puja, baixa de cop, torna a pujar i et fa saltar el stop abans de fer el moviment de veritat, cada accio ara s'analitza tambe pel seu **regim de mercat**:

- **TENDENCIA**: la majoria del moviment ha anat en la mateixa direccio (Efficiency Ratio alt).
- **LATERAL_TRANQUIL**: sense tendencia clara, pero tampoc soroll excessiu.
- **LATERAL_CAOTIC (whipsaw)**: moltes reversions de direccio i Efficiency Ratio molt baix — exactament el patro que fa saltar stops ajustats sense que la tesi d'entrada fos incorrecta.

Quan una accio esta en `LATERAL_CAOTIC`, el punt d'entrada es marca com **"ALT RISC DE WHIPSAW"** (⚠️) independentment de si el score era alt, i la referencia de risc suggerida s'eixampla automaticament fent servir l'ATR (rang mitja per barra) en lloc d'un nivell ajustat al VWAP o al minim del dia.

### Seguiment dedicat d'un valor concret (`watch_ticker`)

Si vols vigilar de prop un valor concret (p.ex. Grifols) amb tot el detall, encara que no surti al TOP 5 general perque el seu score no sigui prou alt:

```python
from main import watch_ticker
watch_ticker("GRIFOLS", "GRF.MC", market="IBEX35")
```

Aixo et dona el detall complet nomes d'aquest valor: recomanacio, punt d'entrada, VWAP, rang del dia, Efficiency Ratio, nombre de reversions, ATR i la referencia de risc suggerida — sense dependre de si guanya o no el rànquing general d'aquell moment.

### Analitzar diversos mercats alhora

`config.MARKETS_TO_RUN` defineix quins mercats s'analitzen quan crides `run_multi_market()` sense arguments (per defecte `["IBEX35", "NASDAQ"]`). Cada mercat fa servir el seu propi univers d'accions (`config.MARKET_STOCK_UNIVERSES`) i la seva moneda (`config.MARKET_CURRENCY`), de manera que l'informe final mostra els dos blocs seguits, cadascun amb el seu rànquing de COMPRAR/VIGILAR/EVITAR.

### Comparar dues captures en el temps (`compare.py`)

Per no dependre nomes d'una foto fixa, pots capturar l'analisi en dos moments (p.ex. amb 10 minuts de diferencia) i veure com evoluciona cada accio:

```python
from compare import take_snapshot, compare_latest

take_snapshot()      # 1a captura, ara
# ... espera 10 minuts ...
take_snapshot()      # 2a captura
compare_latest()      # taula amb delta de score, preu, volum i canvis de recomanacio
```

`compare_latest(only_changed=True)` nomes mostra les accions on el score s'ha mogut o la recomanacio ha canviat, per centrar-se en el que realment es mou. El text de sortida es net i es pot copiar tal qual a ChatGPT o un altre assistent per demanar una segona opinio. Les snapshots es guarden en memoria durant la sessio de Colab (a `compare.SNAPSHOTS`) i es perden si reinicies el runtime.

## Com funciona el score

Score final = 30% Volum + 30% Força relativa + 20% Notícies + 20% Energia (pesos definits a `config.SCORE_WEIGHTS`, fàcilment ajustables).

- **≥ 75** → COMPRAR
- **55–74** → VIGILAR
- **< 55** → EVITAR

Cada recomanació sempre porta els 4 motius que la justifiquen (mai un score sense explicació).

## Ampliar l'univers o el mercat

- Més accions de l'IBEX: afegeix entrades a `config.STOCK_UNIVERSE`.
- Nou mercat (NASDAQ, SP500, DAX...): afegeix una entrada a `config.MARKET_INDEX_TICKERS` i canvia `ACTIVE_MARKET`.

## Preparat per la Fase 2

L'arquitectura modular (cada peça = un mòdul amb dataclasses d'entrada/sortida clares) permet afegir sense reescriure res:
- Backtesting (nou mòdul que reutilitza `data_loader` + `scoring` sobre dades històriques)
- Estadística / Machine Learning (nou mòdul que consumeix `PriceSnapshot`/`StockReport`)
- Probabilitat de continuació, objectiu de preu, stop-loss, gestió monetària (nous camps a `ScoreBreakdown`/`StockReport`)
- Altres mercats (ja contemplat a `config.py`)

## Notes importants

- Totes les fonts són gratuïtes (yfinance + Google News RSS). Cap API de pagament.
- Si el mercat és tancat o yfinance no retorna dades, els mòduls es degraden amb gràcia (scores neutres) en lloc de trencar el programa.
- Aquesta és una eina de suport a la decisió, no prediu el futur ni executa ordres.

## Filtre "nomes llargs" (afegit)

Com que només operes llargs, si la tendència dominant d'avui d'una acció és **BAIXISTA** (Fibonacci calculat sobre el rang del dia), la recomanació es sobreescriu automàticament a **EVITAR**, encara que el score dels 4 pilars fos alt. Es pot desactivar posant `LONG_ONLY_MODE = False` a `config.py`. L'informe també prioritza ara COMPRAR > VIGILAR > EVITAR abans que el score cru, perquè les accions bloquejades pel filtre no ocupin llocs del TOP N desplaçant oportunitats realment operables.

## Fibonacci mensual + horitzó (afegit)

Nou: cada acció ara calcula també un **Fibonacci mensual** (rang de fons, últim mes) a més de l'intradia, i un nou mòdul `horizon_advisor.py` els combina per suggerir:

- **CANDIDATA A SWING**: el moviment d'avui va a favor de la tendència de fons i el preu encara té marge fins al proper nivell mensual important → es pot considerar mantenir-la més d'un dia.
- **NOMES INTRADIA**: o bé el moviment d'avui va en contra de la tendència mensual, o bé el preu ja està a prop d'un sostre/suport de fons → millor tancar en acabar la sessió.

Això és 100% complementari: no canvia la decisió d'entrar o no (això ho decideix el filtre nomes-llargs + el score), només et diu **quant de temps té sentit aguantar-hi** un cop dins. Configurable a `config.py`: `MONTHLY_LOOKBACK_PERIOD` (per defecte "1mo") i `MONTHLY_LEVEL_PROXIMITY_PCT` (per defecte 2%).

**Nota de rendiment:** això afegeix una crida extra a Yahoo Finance per acció (dades diàries d'un mes). Amb pocs valors no hi ha problema; si algun dia amplies l'univers, considera afegir un `time.sleep()` entre accions com al projecte de l'IBEX35 complet.

## Contrast de qualitat del rang mensual (afegit)

Nou mòdul `range_quality.py`: contrasta si el rang mensual (màxim/mínim) que fa servir el Fibonacci mensual és fiable, sense desqualificar-lo automàticament. Detecta:

1. **Historial curt** (`config.RANGE_QUALITY_MIN_TRADING_DAYS`, per defecte 15 sessions): possible sortida a borsa recent.
2. **Salt d'un sol dia** per sobre de `config.RANGE_QUALITY_GAP_WARNING_PCT` (per defecte 8%): possible OPA, ampliació de capital o resultat extraordinari.
3. Si aquest salt **coincideix amb el màxim o mínim actual** del rang (és a dir, si el "nivell important" és en realitat soroll d'un dia).
4. Contrasta també amb `news.py`: si la categoria de notícia més rellevant d'avui és "OPA".

Surt com a etiqueta ALTA/MITJANA/BAIXA amb els motius concrets detectats, sempre just després de l'horitzó suggerit al detall de cada acció. No canvia cap recomanació automàticament — és informatiu, perquè decideixis tu quant fiar-te del Fibonacci mensual abans de confiar-hi per allargar una posició.
