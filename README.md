# Tipo de cambio FIX peso-dólar (Banxico)

Proyecto para descargar y analizar el tipo de cambio FIX pesos por dólar de
E.U.A. de los últimos 10 años, con datos diarios del Sistema de Información
Económica (SIE) del Banco de México.

## Fuente de datos

| | |
|---|---|
| Fuente | [API SIE de Banxico](https://www.banxico.org.mx/SieAPIRest/service/v1/) |
| Serie | `SF43718`: tipo de cambio para solventar obligaciones denominadas en moneda extranjera, fecha de determinación (FIX) |
| Unidades | Pesos por dólar de E.U.A. |
| Frecuencia | Diaria (días hábiles bancarios) |

Banxico determina el FIX cada día hábil bancario y lo publica en el Diario
Oficial de la Federación el día hábil siguiente. Esta serie está indexada por
la **fecha de determinación**.

## Estructura

```
.
├── configurar_entorno.py   # crea .venv, instala dependencias y genera .env
├── descarga_banxico.py     # descarga la serie SF43718 desde la API SIE
├── tc_banxico.csv          # datos brutos (lo genera descarga_banxico.py)
├── requirements.txt        # librerías del proyecto
├── .env.example            # plantilla para el token de Banxico
├── LICENSE
└── README.md
```

## Configuración

Requisitos: Python 3.10 o superior.

1. Solicita un token para la API SIE en
   <https://www.banxico.org.mx/SieAPIRest/service/v1/token>.
2. Ejecuta el script de configuración:

   ```bash
   python configurar_entorno.py
   ```

   El script genera `.env` con tu token (lo pide en pantalla o lo toma de la
   variable de entorno `BANXICO_TOKEN`), crea el entorno virtual `.venv`,
   instala las librerías de `requirements.txt` y verifica que se importen. Se
   puede volver a ejecutar sin riesgo: no sobrescribe `.env` ni recrea `.venv`.
3. Activa el entorno:

   ```bash
   source .venv/bin/activate      # Linux / macOS
   .venv\Scripts\activate         # Windows
   ```

`.env` está en `.gitignore`: el token nunca debe subirse al repositorio.

## Descarga de datos

```bash
python descarga_banxico.py                                   # últimos 10 años hasta hoy
python descarga_banxico.py --inicio 2016-01-01 --fin 2025-12-31
```

El resultado se guarda en `tc_banxico.csv`:

| Columna | Descripción |
|---|---|
| `fecha` | Fecha de determinación del FIX (`AAAA-MM-DD`) |
| `tipo_cambio` | Pesos por dólar de E.U.A. |

Son datos brutos: una fila por cada observación publicada por Banxico, sin
rellenar fines de semana ni días inhábiles. Solo se normaliza el formato: la
fecha pasa de `dd/mm/aaaa` a ISO 8601 y el valor a número. Si Banxico reporta
un valor como `N/E` (no existe), la celda queda vacía.

Para leerlos en pandas:

```python
import pandas as pd

tc = pd.read_csv("tc_banxico.csv", parse_dates=["fecha"], index_col="fecha")
```

## Librerías

| Uso | Librerías |
|---|---|
| Descarga | `requests`, `python-dotenv` |
| Manejo de datos | `numpy`, `pandas` |
| Estadística y econometría | `scipy`, `statsmodels`, `arch` (modelos ARCH/GARCH) |
| Gráficas | `matplotlib` |

## Licencia

El código se distribuye bajo la licencia MIT (ver [LICENSE](LICENSE)). Los
datos provienen del Banco de México y están sujetos a sus términos de uso.
