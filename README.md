# ⚽ 2026 World Cup Predictor

Predictor abierto de los partidos del Mundial 2026. Por cada partido estima el
**favorito**, los **goles esperados**, las **probabilidades 1X2** y los **marcadores más probables**.

🔗 **Pruébalo en vivo:** **https://oscar-wc-predictor.vercel.app/**

Lo interesante no es solo lo que predice, sino **cómo lo predice**: el modelo está pensado para ser
transparente (nada de cajas negras) y, sobre todo, para **evolucionar a medida que se juega el torneo**.

## Cómo funciona: un modelo en dos fases

Un Mundial tiene un problema incómodo para el machine learning: cada selección juega poquísimo (3
partidos en la fase de grupos). No hay datos suficientes para que un modelo aprenda "de cero" quién es
bueno. La solución es arrancar con conocimiento previo y dejar que los datos vayan tomando el mando:

- **Fase 1 — pre-entrenada (antes de que se juegue nada).** El prior no es una tabla a mano: un GLM de
  **Poisson** se pre-entrena con los **partidos internacionales recientes** (clasificación, Nations
  League, amistosos…) y estima el ataque/defensa objetivo de cada selección. El modelo llega al Mundial
  "caliente", sin *cold start*. *(Ver `scripts/build_prior.py` y `app/model/international_ratings.json`.)*
- **Fase 2 — ajustada con el Mundial (en cuanto hay partidos jugados).** Otro GLM de Poisson aprende la
  fuerza *real* de cada selección con los goles del propio Mundial. Como hay pocos partidos, no nos
  fiamos de ellos a ciegas: lo aprendido se **mezcla** con el prior mediante *shrinkage*, y el peso de
  los datos del torneo **crece** con cada partido jugado.

Es decir, al principio del torneo manda el prior (lo aprendido de los internacionales) y, conforme
avanza, mandan los datos del propio Mundial. Ese ajuste gradual es el corazón del proyecto.

## Arquitectura

```
┌────────────────┐ 1 vez/día   ┌──────────────────┐   POST /admin/recompute   ┌─────────────────┐
│ GitHub Actions │ ──────────▶ │ Backend (Render) │ ───── 1 llamada/día ────▶ │ football-data.org│
│  (cron diario) │             │  FastAPI + modelo │                           └─────────────────┘
└────────────────┘             │  caché JSON       │
                              │  rate limit/IP    │
                              └──────────────────┘
                                       ▲ GET /predictions (barato, solo lee la caché)
                                       │   · rate limit 60/min por IP (slowapi)
                              ┌──────────────────┐
                              │ Frontend (Vercel) │  ← lo que ve cada visita
                              └──────────────────┘
```

La idea central es separar el **cálculo** (caro) de la **lectura** (barata):

- La fuente de datos gratuita (`football-data.org`) tiene un límite bajo de peticiones. Si cada visita
  a la web llamara a esa API, se agotaría en segundos.
- Por eso el cálculo pesado (traer los datos del día + correr el modelo) se hace **una sola vez al día**
  y su resultado se **congela en una caché JSON**. Lo dispara un cron de GitHub Actions con un `POST` a
  `/admin/recompute`, protegido por un token secreto y por un *guard* de fecha (aunque se llame de más,
  solo la primera vez del día toca la API externa).
- Cada visitante solo hace un `GET /predictions`, que **lee esa caché y la devuelve** sin tocar nunca
  la API de fútbol. Da igual que entren diez o diez mil personas: para la fuente externa, es una
  llamada al día.
- Como `/predictions` es público, lleva un **rate limit por IP con [slowapi](https://github.com/laurentS/slowapi)**
  (60 peticiones/minuto): un usuario normal ni lo nota, pero evita que un cliente abusivo machaque el
  endpoint y tumbe el backend. La IP real se lee de `X-Forwarded-For` (uvicorn corre tras el proxy de Render).

```
backend/   FastAPI + modelo Poisson/GLM   → desplegado en Render
frontend/  React + Vite + Tailwind        → desplegado en Vercel
.github/workflows/daily-recompute.yml     → cron diario que dispara el recompute
```

## El modelo en detalle

Todo el modelo es una tubería: **fuerza de cada selección → goles esperados → matriz de marcadores →
1X2 y favorito**. Lo único que cambia entre la fase 1 y la 2 es de dónde sale la "fuerza"; el resto del
cálculo es idéntico.

1. **Goles esperados (λ).** Para cada equipo se estima su número esperado de goles en el partido:

   ```
   λ = baseline × ataque_propio × defensa_rival
   ```

   `baseline` es la media de goles por equipo en el torneo; `ataque` y `defensa` son multiplicadores
   centrados en 1.0 (un ataque > 1 marca por encima de la media; una defensa rival > 1 significa que ese
   rival encaja mucho, lo que sube tus goles esperados). La ventaja de campo solo se aplica a las
   selecciones **anfitrionas** (EE. UU., Canadá y México), que son las únicas que juegan en su país; el
   resto del torneo es en sede neutral. *(Ver `app/model/poisson.py` y `app/model/strength.py`.)*

2. **Matriz de marcadores.** Con las dos λ (local y visitante), una distribución de **Poisson** da la
   probabilidad de cada marcador exacto `P(local=i, visitante=j)`. Sumando las celdas correspondientes
   salen las probabilidades de victoria local, empate y visitante (el **1X2**), el **favorito** y los
   marcadores más probables. Se aplica la corrección de **Dixon-Coles**, que ajusta los marcadores bajos
   (0-0, 1-0, 0-1, 1-1) donde el Poisson puro se queda corto.

3. **Aprendizaje (fase 2).** En cuanto hay suficientes partidos jugados, `app/model/train.py` ajusta un
   **GLM de Poisson** sobre los goles reales: `goles ~ ataque(equipo) + defensa(rival) + local`. Los
   coeficientes ajustados *son* la fuerza ofensiva y defensiva aprendida de cada selección, expresada en
   la misma escala (multiplicadores centrados en 1.0) que usa el prior, para que el resto de la tubería
   no cambie.

4. **Shrinkage (la mezcla).** La fuerza final de cada selección es una media ponderada entre su prior
   (el pre-entrenado con internacionales) y lo aprendido del propio Mundial por el GLM:

   ```
   peso_de_los_datos = n / (n + k)
   ```

   donde `n` son los partidos jugados por esa selección y `k` actúa como "partidos virtuales" del prior.
   Con pocos partidos el peso es bajo y manda el prior; con muchos, manda lo observado. Así un 3-0
   puntual no convierte a nadie en favorito de la noche a la mañana. *(Ver `app/model/blend.py`.)*

5. **Acierto / fallo.** En cada recálculo, para los partidos ya jugados se compara el favorito predicho
   con el resultado real y se acumula un porcentaje de acierto, visible en la web.

## Licencia

MIT.
</content>
