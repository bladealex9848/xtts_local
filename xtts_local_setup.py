#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XTTS WebUI: Implementación Local Optimizada
-------------------------------------------
Script integral para configuración, instalación y ejecución de XTTS WebUI
en entornos locales con manejo de dependencias y parches de compatibilidad.
"""

import os
import sys
import subprocess
import argparse
import shutil
import time
from pathlib import Path
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("XTTS-Setup")

# Rutas principales
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
XTTS_DIR = BASE_DIR / "xtts-webui"
MODEL_DIR = XTTS_DIR / "model"
VOICE_DIR = BASE_DIR / "voice_samples"
TEMP_DIR = BASE_DIR / "temp"

# URLs de recursos
MODEL_URL = "https://huggingface.co/IAsistemofinteres/xtts_model/resolve/main/model.zip"
VOICES_URL = "https://huggingface.co/datasets/IAsistemofinteres/vz/resolve/main/vc.zip"
REPO_URL = "https://huggingface.co/spaces/IAsistemofinteres/xtts-webui"


def run_command(command, desc=None, check=True, shell=False):
    """Ejecuta un comando y maneja errores apropiadamente"""
    if desc:
        logger.info(f"{desc}...")

    try:
        if isinstance(command, list) and not shell:
            result = subprocess.run(
                command, check=check, capture_output=True, text=True
            )
        else:
            result = subprocess.run(
                command, shell=True, check=check, capture_output=True, text=True
            )

        if result.stdout.strip():
            logger.debug(result.stdout)

        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Error al ejecutar comando: {e}")
        logger.error(f"Salida de error: {e.stderr}")
        if check:
            sys.exit(1)
        return None


def check_python_version():
    """Verifica que la versión de Python sea compatible"""
    if sys.version_info < (3, 9):
        logger.error("Se requiere Python 3.9 o superior")
        sys.exit(1)
    logger.info(f"Versión de Python compatible: {sys.version}")


def setup_environment():
    """Prepara el entorno para la instalación"""
    # Crear directorios necesarios
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(VOICE_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    logger.info(f"Directorios de trabajo creados en {BASE_DIR}")


def install_system_dependencies():
    """Instala dependencias del sistema operativo"""
    if sys.platform.startswith("linux"):
        logger.info("Instalando dependencias del sistema en Linux...")
        run_command(
            "apt-get update && apt-get install -y libegl1 libopengl0 libxcb-cursor0 ffmpeg",
            desc="Instalando librerías del sistema",
            check=False,
            shell=True,
        )
    elif sys.platform == "darwin":
        logger.info("En macOS, instale las dependencias con: brew install ffmpeg")
    elif sys.platform == "win32":
        logger.info(
            "En Windows, asegúrese de tener instalado FFmpeg y disponible en PATH"
        )

    logger.info("Dependencias del sistema configuradas")


def clone_repository():
    """Clona el repositorio de XTTS WebUI"""
    if XTTS_DIR.exists():
        logger.info("Repositorio ya existente, actualizando...")
        os.chdir(XTTS_DIR)
        run_command(["git", "pull"], desc="Actualizando repositorio")
    else:
        logger.info("Clonando repositorio XTTS WebUI...")
        run_command(
            ["git", "clone", REPO_URL, str(XTTS_DIR)], desc="Clonando repositorio"
        )


def create_virtual_environment():
    """Crea un entorno virtual para la instalación"""
    venv_dir = BASE_DIR / "venv"

    if venv_dir.exists():
        logger.info("Entorno virtual ya existente")
        return venv_dir

    logger.info("Creando entorno virtual...")
    run_command(
        [sys.executable, "-m", "venv", str(venv_dir)],
        desc="Configurando entorno virtual",
    )

    logger.info(f"Entorno virtual creado en {venv_dir}")
    return venv_dir


def get_python_executable(venv_dir):
    """Obtiene la ruta al ejecutable Python del entorno virtual"""
    if sys.platform == "win32":
        python_exe = venv_dir / "Scripts" / "python.exe"
    else:
        python_exe = venv_dir / "bin" / "python"

    if not python_exe.exists():
        logger.error(f"No se encontró el ejecutable Python en {python_exe}")
        sys.exit(1)

    return str(python_exe)


def install_python_dependencies(python_exe):
    """Instala las dependencias de Python"""
    logger.info("Instalando dependencias Python...")

    # Instalar dependencias críticas primero
    critical_deps = [
        "transformers==4.33.0",
        "pandas==1.5.3",
        "fastapi==0.103.1",
        "pydantic==2.3.0",
        "gradio==4.44.1",
        "ctranslate2==4.4.0",
    ]

    run_command(
        [python_exe, "-m", "pip", "install", "--upgrade", "pip"],
        desc="Actualizando pip",
    )

    run_command(
        [python_exe, "-m", "pip", "install"] + critical_deps,
        desc="Instalando dependencias críticas",
    )

    # Instalar requisitos del proyecto
    os.chdir(XTTS_DIR)
    run_command(
        [python_exe, "-m", "pip", "install", "-r", "requirements.txt"],
        desc="Instalando requisitos del proyecto",
    )

    logger.info("Dependencias de Python instaladas correctamente")


def download_resources():
    """Descarga modelos y recursos necesarios"""
    # Descargar el modelo principal
    model_zip = TEMP_DIR / "model.zip"
    if not MODEL_DIR.glob("*.json"):  # Verificar si ya existen archivos del modelo
        logger.info("Descargando modelo principal...")
        if sys.platform == "win32":
            import urllib.request

            urllib.request.urlretrieve(MODEL_URL, model_zip)
        else:
            run_command(
                ["wget", "-q", "--show-progress", MODEL_URL, "-O", str(model_zip)],
                desc="Descargando modelo XTTS",
            )

        logger.info("Extrayendo modelo...")
        import zipfile

        with zipfile.ZipFile(model_zip, "r") as zip_ref:
            zip_ref.extractall(MODEL_DIR)

        logger.info("Modelo descargado y extraído correctamente")
    else:
        logger.info("Modelo ya existente, omitiendo descarga")

    # Descargar voces de ejemplo
    voices_zip = TEMP_DIR / "voices.zip"
    if not list(VOICE_DIR.glob("*")):  # Verificar si ya existen archivos de voz
        logger.info("Descargando voces de ejemplo...")
        if sys.platform == "win32":
            import urllib.request

            urllib.request.urlretrieve(VOICES_URL, voices_zip)
        else:
            run_command(
                ["wget", "-q", "--show-progress", VOICES_URL, "-O", str(voices_zip)],
                desc="Descargando voces de ejemplo",
            )

        logger.info("Extrayendo voces de ejemplo...")
        import zipfile

        with zipfile.ZipFile(voices_zip, "r") as zip_ref:
            zip_ref.extractall(VOICE_DIR)

        logger.info("Voces descargadas y extraídas correctamente")
    else:
        logger.info("Voces ya existentes, omitiendo descarga")


def apply_compatibility_patch():
    """Aplica los parches necesarios para la compatibilidad"""
    logger.info("Aplicando parches de compatibilidad...")

    # Crear directorio utils si no existe
    utils_dir = XTTS_DIR / "utils"
    os.makedirs(utils_dir, exist_ok=True)

    # Crear el archivo de compatibilidad
    compat_file = utils_dir / "compatibility.py"
    with open(compat_file, "w", encoding="utf-8") as f:
        f.write(
            """# Patch para resolver el problema de LogitsWarper
import sys
from transformers.generation.logits_process import LogitsProcessor
import transformers
if not hasattr(transformers, 'LogitsWarper'):
    setattr(transformers, 'LogitsWarper', LogitsProcessor)
    print("✅ Compatibilidad LogitsWarper habilitada")
"""
        )

    # Identificar y parchear el archivo gpt_trainer.py
    import site

    site_packages = site.getsitepackages()

    for site_package in site_packages:
        gpt_trainer_path = (
            Path(site_package)
            / "TTS"
            / "tts"
            / "layers"
            / "xtts"
            / "trainer"
            / "gpt_trainer.py"
        )
        if gpt_trainer_path.exists():
            logger.info(f"Aplicando parche a {gpt_trainer_path}")

            # Leer el contenido actual
            with open(gpt_trainer_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Verificar si ya tiene LogitsWarper
            if "LogitsWarper" not in content:
                content = content.replace(
                    "from transformers import",
                    "from transformers import LogitsProcessor as LogitsWarper,",
                )

                # Guardar el archivo modificado
                with open(gpt_trainer_path, "w", encoding="utf-8") as f:
                    f.write(content)

                logger.info("Parche aplicado correctamente")
            else:
                logger.info("Archivo ya parcheado, omitiendo modificación")

            break
    else:
        logger.warning("No se encontró el archivo gpt_trainer.py para aplicar parche")

    logger.info("Parches de compatibilidad aplicados correctamente")


def create_launcher_script(python_exe):
    """Crea un script de lanzamiento para facilitar la ejecución"""
    launcher_path = BASE_DIR / "ejecutar_xtts.py"

    with open(launcher_path, "w", encoding="utf-8") as f:
        f.write(
            f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Launcher for XTTS WebUI
\"\"\"
import os
import sys
import subprocess

def main():
    # Cambiar al directorio del proyecto
    os.chdir("{str(XTTS_DIR).replace(os.sep, '/')}")
    
    # Agregar directorio al path
    sys.path.insert(0, "{str(XTTS_DIR).replace(os.sep, '/')}")
    
    # Importar módulo de compatibilidad
    try:
        from utils.compatibility import *
        print("✓ Módulo de compatibilidad cargado correctamente")
    except ImportError:
        print("⚠️ No se pudo cargar el módulo de compatibilidad")
    
    # Configurar variables de entorno
    os.environ['PYTHONUNBUFFERED'] = '1'
    
    # Ejecutar la interfaz
    print("\\n🚀 Iniciando XTTS WebUI...")
    print("⏳ La inicialización puede tomar hasta 2 minutos en la primera ejecución")
    print("🔗 La interfaz estará disponible en http://localhost:7860 cuando termine de cargar")
    print("-------------------------------------------------------------------")
    
    # Usar subprocess para mantener la interfaz abierta
    process = subprocess.Popen(
        ["{str(python_exe).replace(os.sep, '/')}", "xtts_demo.py", "--port", "7860"]
    )
    
    try:
        # Mantener el proceso ejecutándose
        process.wait()
    except KeyboardInterrupt:
        print("\\n⚠️ Deteniendo XTTS WebUI...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    main()
"""
        )

    # Hacer el script ejecutable en sistemas Unix
    if sys.platform != "win32":
        os.chmod(launcher_path, 0o755)

    logger.info(f"Script de lanzamiento creado en {launcher_path}")
    return launcher_path


def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(
        description="Instalador y configurador de XTTS WebUI para entorno local"
    )
    parser.add_argument(
        "--skip-download", action="store_true", help="Omitir descarga de modelos"
    )
    parser.add_argument(
        "--no-venv", action="store_true", help="No crear entorno virtual"
    )
    args = parser.parse_args()

    logger.info("=== Iniciando configuración de XTTS WebUI para entorno local ===")

    # Verificaciones iniciales
    check_python_version()
    setup_environment()

    # Si no estamos utilizando un entorno virtual existente, crear uno nuevo
    if not args.no_venv:
        venv_dir = create_virtual_environment()
        python_exe = get_python_executable(venv_dir)
    else:
        python_exe = sys.executable
        logger.info(f"Utilizando Python del sistema: {python_exe}")

    # Instalación y configuración
    install_system_dependencies()
    clone_repository()
    install_python_dependencies(python_exe)

    if not args.skip_download:
        download_resources()

    apply_compatibility_patch()
    launcher_path = create_launcher_script(python_exe)

    # Instrucciones finales
    logger.info("\n=== Instalación completa ===")
    logger.info(f"Para iniciar XTTS WebUI, ejecute: {python_exe} {launcher_path}")
    logger.info("La interfaz estará disponible en http://localhost:7860")
    logger.info(
        "Presione Ctrl+C en la terminal para detener la aplicación cuando desee cerrarla"
    )


if __name__ == "__main__":
    main()
