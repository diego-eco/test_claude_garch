"""Configura el entorno de trabajo del proyecto.

Pasos:
    1. Crea ``.env`` a partir de ``.env.example`` con el token de Banxico.
    2. Crea un entorno virtual en ``.venv`` (si no existe).
    3. Instala las dependencias de ``requirements.txt``.
    4. Verifica que las librerías se importen correctamente.

Uso:
    python configurar_entorno.py

El token se toma de la variable de entorno ``BANXICO_TOKEN``; si no está
definida y la terminal es interactiva, se pide en pantalla (Enter para omitir).
Solo usa la biblioteca estándar, así que funciona antes de instalar nada.
"""

from __future__ import annotations

import getpass
import os
import re
import subprocess
import sys
import venv
from pathlib import Path

PYTHON_MINIMO = (3, 10)

RAIZ = Path(__file__).resolve().parent
DIR_VENV = RAIZ / ".venv"
REQUISITOS = RAIZ / "requirements.txt"
ARCHIVO_ENV = RAIZ / ".env"
PLANTILLA_ENV = RAIZ / ".env.example"

# Módulos que deben importarse sin error al terminar la instalación.
MODULOS = ["requests", "dotenv", "numpy", "pandas", "scipy", "statsmodels", "arch", "matplotlib"]


def python_del_venv() -> Path:
    """Ruta al intérprete de Python dentro de ``.venv``."""
    if os.name == "nt":
        return DIR_VENV / "Scripts" / "python.exe"
    return DIR_VENV / "bin" / "python"


def verificar_version_python() -> None:
    if sys.version_info < PYTHON_MINIMO:
        minimo = ".".join(map(str, PYTHON_MINIMO))
        sys.exit(f"Se requiere Python {minimo} o superior; tienes {sys.version.split()[0]}.")


def crear_env() -> None:
    """Genera ``.env`` con el token de Banxico sin sobrescribir uno existente."""
    if ARCHIVO_ENV.exists():
        print("[1/4] .env ya existe; se conserva sin cambios.")
        return

    token = os.environ.get("BANXICO_TOKEN", "").strip()
    if not token and sys.stdin.isatty():
        token = getpass.getpass("Token de la API SIE de Banxico (Enter para omitir): ").strip()

    plantilla = PLANTILLA_ENV.read_text(encoding="utf-8")
    contenido = re.sub(
        r"^BANXICO_TOKEN=.*$", lambda _: f"BANXICO_TOKEN={token}", plantilla, count=1, flags=re.MULTILINE
    )
    ARCHIVO_ENV.write_text(contenido, encoding="utf-8")
    ARCHIVO_ENV.chmod(0o600)  # solo lectura/escritura para el usuario

    if token:
        print("[1/4] .env creado con el token de Banxico.")
    else:
        print("[1/4] .env creado SIN token: edítalo y escribe tu BANXICO_TOKEN antes de descargar datos.")


def crear_venv() -> None:
    if python_del_venv().exists():
        print(f"[2/4] Entorno virtual existente: {DIR_VENV}")
        return
    print(f"[2/4] Creando entorno virtual en {DIR_VENV} ...")
    venv.create(DIR_VENV, with_pip=True)


def instalar_dependencias() -> None:
    print(f"[3/4] Instalando dependencias de {REQUISITOS.name} ...")
    python = str(python_del_venv())
    subprocess.run([python, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([python, "-m", "pip", "install", "-r", str(REQUISITOS)], check=True)


def verificar_instalacion() -> None:
    print("[4/4] Verificando que las librerías se importen ...")
    codigo = "; ".join(f"import {modulo}" for modulo in MODULOS)
    subprocess.run([str(python_del_venv()), "-c", codigo], check=True)
    print("      OK: " + ", ".join(MODULOS))


def main() -> None:
    verificar_version_python()
    crear_env()
    try:
        crear_venv()
        instalar_dependencias()
        verificar_instalacion()
    except subprocess.CalledProcessError as error:
        sys.exit(f"\nFalló el comando: {' '.join(map(str, error.cmd))} (código {error.returncode}).")

    activar = r".venv\Scripts\activate" if os.name == "nt" else "source .venv/bin/activate"
    print(
        "\nEntorno listo. Siguientes pasos:\n"
        f"  {activar}\n"
        "  python descarga_banxico.py"
    )


if __name__ == "__main__":
    main()
