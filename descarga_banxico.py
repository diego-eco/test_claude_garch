"""Descarga el tipo de cambio FIX (serie SF43718) desde la API SIE de Banxico.

Por defecto descarga los últimos 10 años hasta la fecha y guarda los datos
brutos en ``tc_banxico.csv`` con dos columnas:

    fecha        Fecha de determinación del FIX (AAAA-MM-DD).
    tipo_cambio  Pesos por dólar de E.U.A.; vacío si Banxico reporta "N/E".

Uso:
    python descarga_banxico.py
    python descarga_banxico.py --inicio 2016-01-01 --fin 2025-12-31

El token se lee de la variable de entorno ``BANXICO_TOKEN`` o del archivo
``.env`` en la raíz del proyecto (ver ``.env.example``).
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

RAIZ = Path(__file__).resolve().parent
URL_API = "https://www.banxico.org.mx/SieAPIRest/service/v1"
SERIE = "SF43718"  # Tipo de cambio FIX pesos por dólar, fecha de determinación
ANIOS = 10
ARCHIVO_SALIDA = RAIZ / "tc_banxico.csv"
TIMEOUT = 60  # segundos


def restar_anios(fecha: date, anios: int) -> date:
    """Resta años a una fecha; un 29 de febrero pasa a 28 si el año destino no es bisiesto."""
    try:
        return fecha.replace(year=fecha.year - anios)
    except ValueError:
        return fecha.replace(year=fecha.year - anios, day=28)


def leer_token() -> str:
    load_dotenv(RAIZ / ".env")
    token = os.environ.get("BANXICO_TOKEN", "").strip()
    if not token:
        sys.exit("Falta el token de Banxico: defínelo como BANXICO_TOKEN en .env o en tu entorno.")
    return token


def crear_sesion(token: str) -> requests.Session:
    """Sesión HTTP con el token y reintentos ante fallas temporales de la API."""
    reintentos = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=(429, 500, 502, 503, 504),
        raise_on_status=False,  # devuelve la última respuesta para mostrar el error de la API
    )
    sesion = requests.Session()
    sesion.mount("https://", HTTPAdapter(max_retries=reintentos))
    sesion.headers.update({"Bmx-Token": token, "Accept": "application/json"})
    return sesion


def mensaje_de_error(respuesta: requests.Response) -> str:
    """Extrae el mensaje de error de la API; si no viene en JSON, usa el texto crudo."""
    try:
        error = respuesta.json()["error"]
        return f"{error.get('mensaje', '')} {error.get('detalle', '')}".strip()
    except (ValueError, KeyError, TypeError, AttributeError):
        return respuesta.text[:300]


def descargar_serie(
    sesion: requests.Session, serie: str, inicio: date, fin: date
) -> tuple[str, list[dict[str, str]]]:
    """Devuelve el título de la serie y sus observaciones tal como las entrega la API.

    Cada observación es un diccionario ``{"fecha": "dd/mm/aaaa", "dato": "20.1234"}``.
    """
    url = f"{URL_API}/series/{serie}/datos/{inicio:%Y-%m-%d}/{fin:%Y-%m-%d}"
    respuesta = sesion.get(url, params={"locale": "es"}, timeout=TIMEOUT)
    if not respuesta.ok:
        raise RuntimeError(f"la API respondió {respuesta.status_code}: {mensaje_de_error(respuesta)}")

    datos_serie = respuesta.json()["bmx"]["series"][0]
    titulo = " ".join(datos_serie.get("titulo", serie).split())
    return titulo, datos_serie.get("datos", [])


def a_numero(dato: str) -> float:
    """Convierte el valor de la API a número; "N/E" (no existe) se vuelve NaN."""
    if dato == "N/E":
        return float("nan")
    return float(dato.replace(",", ""))


def a_dataframe(observaciones: list[dict[str, str]]) -> pd.DataFrame:
    """Tabla con las observaciones sin limpiar: solo normaliza fecha y valor numérico."""
    return pd.DataFrame(
        {
            "fecha": pd.to_datetime([obs["fecha"] for obs in observaciones], format="%d/%m/%Y"),
            "tipo_cambio": [a_numero(obs["dato"]) for obs in observaciones],
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Descarga el tipo de cambio FIX (SF43718) de Banxico.")
    parser.add_argument(
        "--inicio", type=date.fromisoformat, help=f"fecha inicial AAAA-MM-DD (por defecto: {ANIOS} años antes de --fin)"
    )
    parser.add_argument("--fin", type=date.fromisoformat, help="fecha final AAAA-MM-DD (por defecto: hoy)")
    parser.add_argument(
        "--salida", type=Path, default=ARCHIVO_SALIDA, help=f"CSV de salida (por defecto: {ARCHIVO_SALIDA.name})"
    )
    args = parser.parse_args()

    fin = args.fin or date.today()
    inicio = args.inicio or restar_anios(fin, ANIOS)
    if inicio > fin:
        parser.error("--inicio debe ser anterior o igual a --fin")

    sesion = crear_sesion(leer_token())
    print(f"Descargando {SERIE} del {inicio} al {fin} ...")
    try:
        titulo, observaciones = descargar_serie(sesion, SERIE, inicio, fin)
    except (requests.RequestException, RuntimeError) as error:
        sys.exit(f"No se pudo descargar la serie {SERIE}: {error}")
    if not observaciones:
        sys.exit(f"La API no devolvió observaciones de {SERIE} entre {inicio} y {fin}.")

    df = a_dataframe(observaciones)
    df.to_csv(args.salida, index=False, date_format="%Y-%m-%d")

    ultima = df.iloc[-1]
    print(f"Serie: {titulo}")
    print(
        f"Observaciones: {len(df):,} ({df['fecha'].min():%Y-%m-%d} a {df['fecha'].max():%Y-%m-%d}); "
        f"sin dato (N/E): {df['tipo_cambio'].isna().sum()}"
    )
    print(f"Último FIX: {ultima['tipo_cambio']:.4f} pesos por dólar ({ultima['fecha']:%Y-%m-%d})")
    print(f"Guardado en: {args.salida}")


if __name__ == "__main__":
    main()
