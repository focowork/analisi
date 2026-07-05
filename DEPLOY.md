# Cómo convertirlo en una app para el móvil (opción más rápida)

Se ha añadido `streamlit_app.py`: una interfaz con botones grandes que
envuelve el motor que ya tenías (`main.py`, `compare.py`, etc. — no se ha
tocado su lógica, solo se le ha puesto una cara de app encima).

Hay dos formas de usarla. La **Opción A** es la más simple para tener algo
ya funcionando en el móvil sin depender de tu ordenador.

---

## Opción A — Desplegarla gratis en Streamlit Community Cloud (recomendado)

Resultado: una URL (tipo `https://tu-app.streamlit.app`) que abres desde el
navegador del móvil. Puedes "Añadir a pantalla de inicio" y se comporta
como una app normal (icono, pantalla completa).

**Pasos (una sola vez, ~10 minutos):**

1. Crea una cuenta gratis en [github.com](https://github.com) si no tienes.
2. Crea un repositorio nuevo (puede ser privado) y sube **toda esta carpeta**
   `ibex_engine/` (todos los `.py` + `requirements.txt` + `streamlit_app.py`).
   - Más fácil: en GitHub, botón "Add file" → "Upload files" → arrastra
     todos los archivos.
3. Ve a [share.streamlit.io](https://share.streamlit.io) y entra con tu
   cuenta de GitHub.
4. "New app" → elige tu repositorio → en "Main file path" pon
   `streamlit_app.py` → Deploy.
5. Espera 1-2 minutos mientras instala las dependencias. Te da una URL.
6. Abre esa URL desde el móvil → menú del navegador → "Añadir a pantalla
   de inicio".

**Cada vez que quieras usarla:** abre el icono en el móvil, pulsa
"Analitzar ara". No necesitas Colab ni tu ordenador encendido.

**Notas:**
- El plan gratuito de Streamlit Cloud "duerme" la app si no se usa en
  varios días; el primer acceso del día puede tardar ~30 segundos en
  despertar. Es normal.
- Las snapshots de la pestaña "Snapshots" se guardan solo mientras la
  pestaña del navegador está abierta (igual que antes en Colab: si cierras
  o recargas, se pierden). Esto es intencional, no un fallo.
- Si en el futuro quieres editar el código, puedes hacerlo directamente en
  GitHub o desde tu ordenador y volver a subirlo; Streamlit Cloud
  redespliega solo.

---

## Opción B — Probarla ya mismo en tu ordenador (sin subir nada a internet)

Útil para verla funcionar en 2 minutos antes de decidir si la despliegas.

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Se abrirá en `http://localhost:8501`. Para verla en el móvil sin
desplegarla:
1. Asegúrate de que el móvil está en la **misma red WiFi** que el ordenador.
2. En la terminal donde corre streamlit, busca la línea "Network URL"
   (algo como `http://192.168.1.XX:8501`).
3. Abre esa dirección desde el navegador del móvil.
4. Mientras el ordenador esté encendido y streamlit corriendo, funciona;
   si lo apagas, deja de estar disponible (por eso la Opción A es mejor
   para uso diario real).

---

## ¿Qué hace la app exactamente?

Tres pestañas, cada una llama a funciones que ya existían en tu proyecto:

| Pestaña | Equivale a (Colab) |
|---|---|
| 🔍 Analisi | `run_multi_market()` / `run(market=...)` |
| 🕒 Snapshots | `compare.take_snapshot()` + `compare.compare_latest()` |
| 👁️ Seguiment | `watch_ticker(nombre, ticker, market)` |

No se ha cambiado ninguna lógica de scoring, filtros ni fuentes de datos:
sigue usando yfinance + Google News RSS, gratis, igual que antes.
