#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XTTS WebUI: Implementación Local Optimizada
-------------------------------------------
Script integral para configuración, instalación y ejecución de XTTS WebUI
en entornos locales con manejo robusto de errores y rutas alternativas.

Autor: Alexander
Fecha: 24-03-2025
Versión: 1.1.0
"""

import os
import sys
import subprocess
import argparse
import shutil
import time
from pathlib import Path
import logging
import platform
import tempfile
import json
import traceback

# Configuración de logging con formato mejorado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("xtts_setup.log", mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger("XTTS-Setup")

# Rutas principales con detección de espacios
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
XTTS_DIR = BASE_DIR / "xtts-webui"
MODEL_DIR = XTTS_DIR / "model"
VOICE_DIR = BASE_DIR / "voice_samples"
TEMP_DIR = BASE_DIR / "temp"
CONFIG_FILE = BASE_DIR / "xtts_config.json"

# URLs de recursos
MODEL_URL = "https://huggingface.co/IAsistemofinteres/xtts_model/resolve/main/model.zip"
VOICES_URL = "https://huggingface.co/datasets/IAsistemofinteres/vz/resolve/main/vc.zip"
REPO_URL = "https://huggingface.co/spaces/IAsistemofinteres/xtts-webui"

# Configuración de dependencias directas
CRITICAL_DEPENDENCIES = [
    "transformers==4.33.0",
    "pandas==1.5.3",
    "fastapi==0.103.1",
    "pydantic==2.3.0",
    "gradio==4.44.1",
    "ctranslate2==4.4.0",
]

PROJECT_DEPENDENCIES = [
    "faster_whisper==1.0.3",
    "gradio==4.44.1",
    "spacy==3.7.5",
    "TTS==0.22.0",
    "cutlet",
    "fugashi[unidic-lite]",
]

# Estado de la configuración
config_state = {
    "installed": False,
    "models_downloaded": False,
    "patched": False,
    "last_run": None,
    "python_exe": None,
    "error_log": [],
}


def save_config_state():
    """Guarda el estado actual de la configuración"""
    config_state["last_run"] = time.time()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_state, f, indent=2)
    logger.debug(f"Estado guardado en {CONFIG_FILE}")


def load_config_state():
    """Carga el estado de configuración existente si está disponible"""
    global config_state
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded_state = json.load(f)
                config_state.update(loaded_state)
            logger.debug(f"Estado cargado desde {CONFIG_FILE}")
        except Exception as e:
            logger.warning(f"Error al cargar el estado de configuración: {e}")


def run_command(
    command, desc=None, check=True, shell=False, capture_output=True, verbose=False
):
    """Ejecuta un comando y maneja errores apropiadamente con opciones avanzadas"""
    if desc:
        logger.info(f"{desc}...")

    if verbose:
        logger.debug(f"Ejecutando comando: {command}")

    try:
        if isinstance(command, list) and not shell:
            if capture_output:
                result = subprocess.run(
                    command, check=check, capture_output=True, text=True
                )
            else:
                result = subprocess.run(command, check=check)
        else:
            if capture_output:
                result = subprocess.run(
                    command, shell=True, check=check, capture_output=True, text=True
                )
            else:
                result = subprocess.run(command, shell=True, check=check)

        if capture_output and result.stdout and verbose:
            logger.debug(result.stdout)

        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Error al ejecutar comando: {e}")
        if e.stderr:
            logger.error(f"Salida de error: {e.stderr}")

        # Registrar el error en el estado
        config_state["error_log"].append(
            {
                "timestamp": time.time(),
                "command": str(command),
                "error": str(e),
                "stderr": e.stderr if hasattr(e, "stderr") and e.stderr else None,
            }
        )

        if check:
            logger.warning("Fallo en el comando. Continuando con el siguiente paso...")
            if "requirements.txt" in str(e) and "No such file or directory" in str(
                e.stderr
            ):
                logger.info(
                    "⚠️ No se encontró el archivo requirements.txt. Se utilizará instalación directa de dependencias."
                )
                return None
            # No terminamos el script para manejar errores específicos
        return None


def check_python_version():
    """Verifica que la versión de Python sea compatible"""
    if sys.version_info < (3, 9):
        logger.error("Se requiere Python 3.9 o superior")
        logger.info("Instale una versión compatible de Python e intente nuevamente")
        sys.exit(1)
    logger.info(f"Versión de Python compatible: {sys.version}")


def setup_environment():
    """Prepara el entorno para la instalación con verificación de permisos"""
    # Verificar permisos de escritura
    try:
        # Crear directorios necesarios
        for directory in [MODEL_DIR, VOICE_DIR, TEMP_DIR]:
            os.makedirs(directory, exist_ok=True)

        # Verificar escritura
        test_file = TEMP_DIR / "write_test.tmp"
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)

        logger.info(f"Directorios de trabajo creados en {BASE_DIR}")
    except PermissionError:
        logger.error(f"Error de permisos al escribir en {BASE_DIR}")
        logger.info("Ejecute el script con permisos adecuados o elija otra ubicación")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error al configurar el entorno: {e}")
        logger.info("Verificando directorios individualmente...")

        # Intentar crear cada directorio por separado para identificar problemas específicos
        for directory in [MODEL_DIR, VOICE_DIR, TEMP_DIR]:
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"✓ Directorio {directory} creado correctamente")
            except Exception as e:
                logger.error(f"✗ No se pudo crear {directory}: {e}")


def detect_ffmpeg():
    """Detecta la instalación de FFmpeg y sugiere cómo instalarlo si falta"""
    try:
        result = run_command(
            ["ffmpeg", "-version"], desc="Verificando FFmpeg", check=False
        )
        if result and result.returncode == 0:
            logger.info("✓ FFmpeg detectado correctamente")
            return True
    except:
        pass

    logger.warning(
        "⚠️ FFmpeg no encontrado, que es necesario para el procesamiento de audio"
    )

    if sys.platform == "darwin":
        logger.info("Instale FFmpeg con: brew install ffmpeg")
    elif sys.platform.startswith("linux"):
        logger.info("Instale FFmpeg con: sudo apt-get install ffmpeg (Ubuntu/Debian)")
        logger.info("O: sudo yum install ffmpeg (CentOS/RHEL/Fedora)")
    elif sys.platform == "win32":
        logger.info("Descargue FFmpeg desde https://ffmpeg.org/download.html")
        logger.info("Y agregue la carpeta bin al PATH del sistema")

    return False


def install_system_dependencies():
    """Instala dependencias del sistema operativo con verificación de FFmpeg"""
    if sys.platform.startswith("linux"):
        logger.info("Instalando dependencias del sistema en Linux...")
        try:
            run_command(
                "apt-get update && apt-get install -y libegl1 libopengl0 libxcb-cursor0 ffmpeg",
                desc="Instalando librerías del sistema",
                check=False,
                shell=True,
            )
        except Exception as e:
            logger.warning(
                f"No se pudieron instalar todas las dependencias del sistema: {e}"
            )
            logger.info("Algunas características podrían no funcionar correctamente")
    elif sys.platform == "darwin":
        logger.info("Verificando dependencias en macOS...")
        # Verificar si Homebrew está instalado
        brew_installed = run_command("which brew", shell=True, check=False)
        if brew_installed and brew_installed.returncode == 0:
            logger.info(
                "Homebrew detectado, se puede instalar FFmpeg con: brew install ffmpeg"
            )
            # Opcional: instalar automáticamente
            # run_command("brew install ffmpeg", shell=True, check=False)
        else:
            logger.info("Homebrew no detectado. Instálelo desde https://brew.sh/")
    elif sys.platform == "win32":
        logger.info(
            "En Windows, asegúrese de tener instalado FFmpeg y disponible en PATH"
        )

    # Verificar FFmpeg independientemente del sistema operativo
    detect_ffmpeg()

    logger.info("Dependencias del sistema configuradas")


def clone_repository():
    """Clona el repositorio de XTTS WebUI con manejo de errores mejorado"""
    if XTTS_DIR.exists():
        logger.info("Repositorio ya existente, actualizando...")
        try:
            os.chdir(XTTS_DIR)
            run_command(["git", "pull"], desc="Actualizando repositorio")
        except Exception as e:
            logger.warning(f"Error al actualizar el repositorio: {e}")
            logger.info("Continuando con la versión existente")
    else:
        logger.info("Clonando repositorio XTTS WebUI...")
        try:
            run_command(
                ["git", "clone", REPO_URL, str(XTTS_DIR)], desc="Clonando repositorio"
            )
        except Exception as e:
            logger.error(f"Error al clonar el repositorio: {e}")
            logger.info("Intentando métodos alternativos...")

            # Alternativa: Descarga directa si git falla
            try:
                import requests
                from zipfile import ZipFile

                # URL alternativa para descargar como ZIP
                zip_url = "https://huggingface.co/spaces/IAsistemofinteres/xtts-webui/archive/main.zip"
                zip_path = TEMP_DIR / "xtts-webui.zip"

                logger.info(f"Descargando ZIP del repositorio desde {zip_url}")
                response = requests.get(zip_url, stream=True)
                with open(zip_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                logger.info("Extrayendo repositorio...")
                with ZipFile(zip_path, "r") as zip_ref:
                    temp_dir = TEMP_DIR / "extracted"
                    os.makedirs(temp_dir, exist_ok=True)
                    zip_ref.extractall(temp_dir)

                    # Encontrar el directorio principal dentro del ZIP
                    extracted_dirs = [
                        d
                        for d in os.listdir(temp_dir)
                        if os.path.isdir(os.path.join(temp_dir, d))
                    ]
                    if extracted_dirs:
                        # Mover al destino final
                        shutil.move(os.path.join(temp_dir, extracted_dirs[0]), XTTS_DIR)
                        logger.info(f"Repositorio extraído en {XTTS_DIR}")
                    else:
                        raise Exception(
                            "No se encontró el directorio principal en el ZIP"
                        )

                # Limpiar archivos temporales
                os.remove(zip_path)
                shutil.rmtree(temp_dir, ignore_errors=True)

            except Exception as e2:
                logger.error(f"Ambos métodos de descarga fallaron: {e2}")
                logger.error(
                    "No se pudo obtener el repositorio. Verifique su conexión a Internet"
                )
                sys.exit(1)


def create_virtual_environment():
    """Crea un entorno virtual para la instalación con verificación detallada"""
    venv_dir = BASE_DIR / "venv"

    if venv_dir.exists():
        logger.info("Entorno virtual ya existente")

        # Verificar que el entorno virtual sea utilizable
        if sys.platform == "win32":
            python_exe = venv_dir / "Scripts" / "python.exe"
            pip_exe = venv_dir / "Scripts" / "pip.exe"
        else:
            python_exe = venv_dir / "bin" / "python"
            pip_exe = venv_dir / "bin" / "pip"

        if not python_exe.exists() or not pip_exe.exists():
            logger.warning("Entorno virtual parece estar dañado o incompleto")
            logger.info("Recreando entorno virtual...")
            try:
                shutil.rmtree(venv_dir)
            except Exception as e:
                logger.error(f"No se pudo eliminar el entorno virtual existente: {e}")
                logger.info(
                    "Por favor, elimine manualmente el directorio venv e intente nuevamente"
                )
                sys.exit(1)
            # Continuar con la creación
        else:
            return venv_dir

    logger.info("Creando entorno virtual...")
    try:
        run_command(
            [sys.executable, "-m", "venv", str(venv_dir)],
            desc="Configurando entorno virtual",
        )

        logger.info(f"Entorno virtual creado en {venv_dir}")
    except Exception as e:
        logger.error(f"Error al crear entorno virtual: {e}")
        logger.info("Intentando método alternativo...")

        try:
            # Intentar con virtualenv si venv falla
            try:
                import virtualenv
            except ImportError:
                run_command(
                    [sys.executable, "-m", "pip", "install", "virtualenv"],
                    desc="Instalando virtualenv",
                )

            run_command(
                [sys.executable, "-m", "virtualenv", str(venv_dir)],
                desc="Creando entorno virtual con virtualenv",
            )

            logger.info(f"Entorno virtual creado con virtualenv en {venv_dir}")
        except Exception as e2:
            logger.error(f"Ambos métodos de creación de entorno virtual fallaron: {e2}")
            logger.info("Continuando sin entorno virtual. La instalación será global.")
            return None

    return venv_dir


def get_python_executable(venv_dir):
    """Obtiene la ruta al ejecutable Python del entorno virtual con verificación"""
    if venv_dir is None:
        logger.warning(
            "No se está utilizando un entorno virtual. Se usará Python del sistema."
        )
        return sys.executable

    if sys.platform == "win32":
        python_exe = venv_dir / "Scripts" / "python.exe"
    else:
        python_exe = venv_dir / "bin" / "python"

    if not python_exe.exists():
        logger.error(f"No se encontró el ejecutable Python en {python_exe}")
        logger.info("Se usará Python del sistema como alternativa.")
        return sys.executable

    # Verificar que el ejecutable funcione
    try:
        result = run_command([str(python_exe), "--version"], check=False)
        if result and result.returncode == 0:
            logger.debug(f"Verificación de Python: {result.stdout.strip()}")
        else:
            logger.warning(
                f"El ejecutable Python existe pero no responde correctamente"
            )
            logger.info("Se usará Python del sistema como alternativa.")
            return sys.executable
    except Exception:
        logger.warning(f"Error al verificar el ejecutable Python")
        logger.info("Se usará Python del sistema como alternativa.")
        return sys.executable

    # Guardar en el estado
    config_state["python_exe"] = str(python_exe)

    return str(python_exe)


def create_requirements_file():
    """Crea el archivo requirements.txt si no existe"""
    req_file = XTTS_DIR / "requirements.txt"

    if req_file.exists():
        logger.info(f"Archivo requirements.txt encontrado en {req_file}")
        return req_file

    logger.info("Creando archivo requirements.txt...")
    try:
        with open(req_file, "w", encoding="utf-8") as f:
            f.write("\n".join(PROJECT_DEPENDENCIES))

        logger.info(f"Archivo requirements.txt creado en {req_file}")
        return req_file
    except Exception as e:
        logger.error(f"Error al crear requirements.txt: {e}")
        logger.info("Se utilizará instalación directa de dependencias")
        return None


def install_python_dependencies(python_exe):
    """Instala las dependencias de Python con múltiples estrategias de recuperación"""
    logger.info("Instalando dependencias Python...")

    # Actualizar pip primero
    try:
        run_command(
            [python_exe, "-m", "pip", "install", "--upgrade", "pip"],
            desc="Actualizando pip",
        )
    except Exception as e:
        logger.warning(f"Error al actualizar pip: {e}")
        logger.info("Continuando con la versión actual de pip")

    # Instalar dependencias críticas primero
    try:
        run_command(
            [python_exe, "-m", "pip", "install"] + CRITICAL_DEPENDENCIES,
            desc="Instalando dependencias críticas",
        )
    except Exception as e:
        logger.error(f"Error al instalar dependencias críticas: {e}")
        logger.info("Intentando instalación individual de cada dependencia...")

        # Intentar instalar cada dependencia por separado
        for dep in CRITICAL_DEPENDENCIES:
            try:
                run_command(
                    [python_exe, "-m", "pip", "install", dep], desc=f"Instalando {dep}"
                )
                logger.info(f"✓ {dep} instalado correctamente")
            except Exception as e_dep:
                logger.error(f"✗ Error al instalar {dep}: {e_dep}")

    # Instalar requisitos del proyecto
    os.chdir(XTTS_DIR)

    # Método 1: Intentar usar requirements.txt
    req_file = create_requirements_file()

    if req_file and req_file.exists():
        try:
            run_command(
                [python_exe, "-m", "pip", "install", "-r", str(req_file)],
                desc="Instalando requisitos del proyecto desde requirements.txt",
            )
            logger.info(
                "Dependencias del proyecto instaladas correctamente desde requirements.txt"
            )
            return
        except Exception as e:
            logger.warning(f"Error al instalar desde requirements.txt: {e}")
            logger.info("Intentando método alternativo...")

    # Método 2: Instalación directa de las dependencias del proyecto
    logger.info("Instalando dependencias del proyecto directamente...")
    try:
        run_command(
            [python_exe, "-m", "pip", "install"] + PROJECT_DEPENDENCIES,
            desc="Instalando dependencias del proyecto",
        )
        logger.info("Dependencias del proyecto instaladas correctamente")
    except Exception as e:
        logger.error(f"Error en la instalación directa de dependencias: {e}")
        logger.info("Intentando instalación individual de cada dependencia...")

        # Intentar instalar cada dependencia por separado
        for dep in PROJECT_DEPENDENCIES:
            try:
                run_command(
                    [python_exe, "-m", "pip", "install", dep], desc=f"Instalando {dep}"
                )
                logger.info(f"✓ {dep} instalado correctamente")
            except Exception as e_dep:
                logger.error(f"✗ Error al instalar {dep}: {e_dep}")

    # Actualizar el estado
    config_state["installed"] = True


def download_file(url, output_path, desc="Descargando archivo"):
    """Descarga un archivo con varios métodos y verificación"""
    logger.info(f"{desc} desde {url}")
    output_path = Path(output_path)

    # Método 1: Usar wget si está disponible
    if sys.platform != "win32":
        try:
            result = run_command(
                ["wget", "-q", "--show-progress", url, "-O", str(output_path)],
                desc=desc,
                check=False,
            )
            if (
                result
                and result.returncode == 0
                and output_path.exists()
                and output_path.stat().st_size > 1000
            ):
                logger.info(
                    f"✓ Archivo descargado correctamente con wget ({output_path.stat().st_size / 1024 / 1024:.2f} MB)"
                )
                return True
        except Exception as e:
            logger.warning(f"Error al descargar con wget: {e}")

    # Método 2: Usar curl si está disponible
    if sys.platform != "win32":
        try:
            result = run_command(
                ["curl", "-L", "--silent", "--output", str(output_path), url],
                desc=f"{desc} con curl",
                check=False,
            )
            if (
                result
                and result.returncode == 0
                and output_path.exists()
                and output_path.stat().st_size > 1000
            ):
                logger.info(
                    f"✓ Archivo descargado correctamente con curl ({output_path.stat().st_size / 1024 / 1024:.2f} MB)"
                )
                return True
        except Exception as e:
            logger.warning(f"Error al descargar con curl: {e}")

    # Método 3: Usar requests (método universal)
    try:
        import requests

        logger.info(f"{desc} con requests...")

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get("content-length", 0))
            block_size = 8192
            downloaded = 0

            with open(output_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # Mostrar progreso
                        if total_size > 0:
                            done = int(50 * downloaded / total_size)
                            sys.stdout.write(
                                f"\r[{'=' * done}{' ' * (50-done)}] {downloaded/1024/1024:.2f}/{total_size/1024/1024:.2f} MB"
                            )
                            sys.stdout.flush()

            if output_path.exists() and output_path.stat().st_size > 1000:
                logger.info(
                    f"\n✓ Archivo descargado correctamente con requests ({output_path.stat().st_size / 1024 / 1024:.2f} MB)"
                )
                return True
            else:
                logger.error(f"El archivo descargado parece estar incompleto o dañado")
                return False
    except Exception as e:
        logger.error(f"Error al descargar con requests: {e}")
        return False

    logger.error(f"Todos los métodos de descarga fallaron")
    return False


def download_resources():
    """Descarga modelos y recursos necesarios con verificación de integridad"""
    # Verificar si los modelos ya están presentes
    if MODEL_DIR.exists() and list(MODEL_DIR.glob("*.json")):
        logger.info(f"Archivos de modelo detectados en {MODEL_DIR}")
        logger.info(
            "Omitiendo descarga de modelos. Use --force-download para descargar de nuevo."
        )
        config_state["models_downloaded"] = True
        return True

    # Descargar el modelo principal
    model_zip = TEMP_DIR / "model.zip"
    model_downloaded = download_file(
        MODEL_URL, model_zip, "Descargando modelo principal XTTS"
    )

    if not model_downloaded:
        logger.error("No se pudo descargar el modelo principal")
        logger.info("Por favor, verifique su conexión a Internet e intente nuevamente")
        return False

    # Extraer el modelo
    logger.info("Extrayendo modelo principal...")
    try:
        import zipfile

        with zipfile.ZipFile(model_zip, "r") as zip_ref:
            zip_ref.extractall(MODEL_DIR)

        # Verificar archivos críticos
        critical_files = ["config.json"]
        missing = [f for f in critical_files if not (MODEL_DIR / f).exists()]
        if missing:
            logger.error(
                f"Faltan archivos críticos después de la extracción: {missing}"
            )
            return False
        else:
            logger.info("✓ Modelo extraído correctamente")
    except Exception as e:
        logger.error(f"Error al extraer el modelo: {e}")
        return False

    # Descargar voces de ejemplo
    voices_zip = TEMP_DIR / "voices.zip"
    voices_downloaded = download_file(
        VOICES_URL, voices_zip, "Descargando voces de ejemplo"
    )

    if not voices_downloaded:
        logger.warning("No se pudieron descargar las voces de ejemplo")
        logger.info(
            "La aplicación funcionará, pero no tendrá voces de ejemplo precargadas"
        )
    else:
        # Extraer voces
        logger.info("Extrayendo voces de ejemplo...")
        try:
            import zipfile

            with zipfile.ZipFile(voices_zip, "r") as zip_ref:
                zip_ref.extractall(VOICE_DIR)
            logger.info("✓ Voces extraídas correctamente")
        except Exception as e:
            logger.warning(f"Error al extraer las voces: {e}")
            logger.info(
                "La aplicación funcionará, pero no tendrá voces de ejemplo precargadas"
            )

    # Limpiar archivos temporales
    try:
        if model_zip.exists():
            os.remove(model_zip)
        if voices_zip.exists():
            os.remove(voices_zip)
    except Exception as e:
        logger.warning(f"Error al eliminar archivos temporales: {e}")

    # Actualizar estado
    config_state["models_downloaded"] = True
    return True


def apply_compatibility_patch():
    """Aplica los parches necesarios para la compatibilidad con múltiples verificaciones"""
    logger.info("Aplicando parches de compatibilidad...")

    # Crear directorio utils si no existe
    utils_dir = XTTS_DIR / "utils"
    os.makedirs(utils_dir, exist_ok=True)

    # Crear el archivo de compatibilidad
    compat_file = utils_dir / "compatibility.py"
    compatibility_code = """# Patch para resolver el problema de LogitsWarper
import sys
from transformers.generation.logits_process import LogitsProcessor
import transformers
if not hasattr(transformers, 'LogitsWarper'):
    setattr(transformers, 'LogitsWarper', LogitsProcessor)
    print("✅ Compatibilidad LogitsWarper habilitada")
"""

    try:
        with open(compat_file, "w", encoding="utf-8") as f:
            f.write(compatibility_code)
        logger.info(f"✓ Archivo de compatibilidad creado en {compat_file}")
    except Exception as e:
        logger.error(f"Error al crear archivo de compatibilidad: {e}")
        logger.info("Intentando método alternativo...")

        # Método alternativo usando un archivo temporal
        try:
            import tempfile

            temp_file = tempfile.NamedTemporaryFile(
                delete=False, mode="w", suffix=".py"
            )
            temp_file.write(compatibility_code)
            temp_file.close()

            shutil.copy2(temp_file.name, compat_file)
            os.unlink(temp_file.name)
            logger.info(f"✓ Archivo de compatibilidad creado mediante archivo temporal")
        except Exception as e2:
            logger.error(
                f"Ambos métodos fallaron al crear archivo de compatibilidad: {e2}"
            )
            logger.info("El parche de compatibilidad deberá aplicarse manualmente")

    # Parche directo al módulo de transformers (método de respaldo)
    gpt_trainer_patched = False
    try:
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
                    patched_content = content.replace(
                        "from transformers import",
                        "from transformers import LogitsProcessor as LogitsWarper,",
                    )

                    # Guardar el archivo modificado
                    with open(gpt_trainer_path, "w", encoding="utf-8") as f:
                        f.write(patched_content)

                    logger.info(
                        "✓ Parche aplicado correctamente al archivo gpt_trainer.py"
                    )
                    gpt_trainer_patched = True
                else:
                    logger.info("✓ Archivo gpt_trainer.py ya está parcheado")
                    gpt_trainer_patched = True

                break

        if not gpt_trainer_patched:
            logger.warning(
                "No se encontró el archivo gpt_trainer.py para aplicar parche"
            )
            logger.info("El parche se aplicará dinámicamente durante la ejecución")
    except Exception as e:
        logger.warning(f"Error al aplicar parche a gpt_trainer.py: {e}")
        logger.info("El parche se aplicará dinámicamente durante la ejecución")

    # Aplicar parche dinámico al módulo transformers
    try:
        import transformers
        from transformers.generation.logits_process import LogitsProcessor

        if not hasattr(transformers, "LogitsWarper"):
            setattr(transformers, "LogitsWarper", LogitsProcessor)
            logger.info("✓ Parche dinámico aplicado al módulo transformers")
    except Exception as e:
        logger.warning(f"Error al aplicar parche dinámico: {e}")

    # Actualizar estado
    config_state["patched"] = True
    logger.info("Parches de compatibilidad aplicados correctamente")


def create_launcher_script(python_exe):
    """Crea un script de lanzamiento para facilitar la ejecución con manejo de errores"""
    launcher_path = BASE_DIR / "ejecutar_xtts.py"

    launcher_code = f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Launcher for XTTS WebUI
Creado automáticamente por xtts_local_setup.py
\"\"\"
import os
import sys
import subprocess
import logging
import time
import traceback
import signal

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("xtts_runtime.log", mode="w", encoding="utf-8")
    ]
)
logger = logging.getLogger("XTTS-Runtime")

def signal_handler(sig, frame):
    \"\"\"Manejador de señal para SIGINT (Ctrl+C)\"\"\"
    logger.info("\\n⚠️ Recibida señal de interrupción. Finalizando de forma segura...")
    if 'process' in globals() and process:
        process.terminate()
        try:
            process.wait(timeout=5)
            logger.info("Proceso finalizado correctamente")
        except subprocess.TimeoutExpired:
            logger.warning("El proceso no terminó tras 5 segundos, forzando finalización...")
            process.kill()
    sys.exit(0)

def main():
    \"\"\"Función principal para ejecutar XTTS WebUI\"\"\"
    global process
    
    # Registrar manejador de señal
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Cambiar al directorio del proyecto
        project_dir = "{str(XTTS_DIR).replace(os.sep, '/')}"
        logger.info(f"Cambiando al directorio: {{project_dir}}")
        os.chdir(project_dir)
        
        # Agregar directorio al path
        sys.path.insert(0, project_dir)
        
        # Importar módulo de compatibilidad
        try:
            sys.path.insert(0, os.path.join(project_dir, "utils"))
            from compatibility import *
            logger.info("✓ Módulo de compatibilidad cargado correctamente")
        except ImportError as e:
            logger.warning(f"⚠️ No se pudo cargar el módulo de compatibilidad: {{e}}")
            logger.info("Aplicando parche dinámico...")
            
            # Aplicar parche dinámico si falla la importación
            try:
                import transformers
                from transformers.generation.logits_process import LogitsProcessor
                if not hasattr(transformers, 'LogitsWarper'):
                    setattr(transformers, 'LogitsWarper', LogitsProcessor)
                    logger.info("✓ Parche dinámico aplicado correctamente")
            except Exception as e2:
                logger.error(f"❌ Error al aplicar parche dinámico: {{e2}}")
                logger.warning("Algunas funcionalidades podrían no estar disponibles")
        
        # Verificar modelo
        model_config = os.path.join(project_dir, "model", "config.json")
        if not os.path.exists(model_config):
            logger.error(f"❌ No se encontró el archivo de configuración del modelo en {{model_config}}")
            logger.error("Ejecute xtts_local_setup.py para descargar los modelos necesarios")
            sys.exit(1)
        
        # Configurar variables de entorno
        os.environ['PYTHONUNBUFFERED'] = '1'
        os.environ['GRADIO_ANALYTICS_ENABLED'] = 'False'
        
        # Ejecutar la interfaz
        logger.info("\\n🚀 Iniciando XTTS WebUI...")
        logger.info("⏳ La inicialización puede tomar hasta 2 minutos en la primera ejecución")
        logger.info("🔗 La interfaz estará disponible en http://localhost:7860 cuando termine de cargar")
        logger.info("-------------------------------------------------------------------")
        
        # Usar subprocess para mantener la interfaz abierta
        cmd = ["{str(python_exe).replace(os.sep, '/')}", "xtts_demo.py", "--port", "7860"]
        logger.debug(f"Ejecutando comando: {{' '.join(cmd)}}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Redirigir la salida del proceso para mostrarla en tiempo real
        for line in iter(process.stdout.readline, ''):
            print(line, end='')
            sys.stdout.flush()
            if "Running on local URL:" in line:
                logger.info("\\n✅ Interfaz iniciada correctamente")
            if "Error" in line or "ERROR" in line or "error" in line:
                logger.warning(f"⚠️ Posible error detectado: {{line.strip()}}")
        
        # Esperar a que el proceso termine
        return_code = process.wait()
        if return_code != 0:
            logger.error(f"❌ El proceso terminó con código: {{return_code}}")
        else:
            logger.info("Proceso finalizado correctamente")
    
    except KeyboardInterrupt:
        logger.info("\\n⚠️ Operación interrumpida por el usuario")
        if 'process' in locals() and process:
            logger.info("Finalizando proceso...")
            process.terminate()
            process.wait()
    except Exception as e:
        logger.error(f"❌ Error inesperado: {{e}}")
        logger.error(traceback.format_exc())
        if 'process' in locals() and process:
            process.terminate()
            process.wait()
        sys.exit(1)

if __name__ == "__main__":
    main()
"""

    try:
        with open(launcher_path, "w", encoding="utf-8") as f:
            f.write(launcher_code)

        # Hacer el script ejecutable en sistemas Unix
        if sys.platform != "win32":
            os.chmod(launcher_path, 0o755)

        logger.info(f"✓ Script de lanzamiento creado en {launcher_path}")
        return launcher_path
    except Exception as e:
        logger.error(f"Error al crear script de lanzamiento: {e}")
        logger.info("El script de lanzamiento deberá crearse manualmente")

        # Crear en ubicación alternativa
        try:
            alt_path = TEMP_DIR / "ejecutar_xtts.py"
            with open(alt_path, "w", encoding="utf-8") as f:
                f.write(launcher_code)

            if sys.platform != "win32":
                os.chmod(alt_path, 0o755)

            logger.info(
                f"✓ Script de lanzamiento creado en ubicación alternativa: {alt_path}"
            )
            return alt_path
        except Exception as e2:
            logger.error(f"Error al crear script alternativo: {e2}")
            return None


def main():
    """Función principal del script con gestión de errores global"""
    parser = argparse.ArgumentParser(
        description="Instalador y configurador de XTTS WebUI para entorno local"
    )
    parser.add_argument(
        "--skip-download", action="store_true", help="Omitir descarga de modelos"
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Forzar descarga de modelos aunque ya existan",
    )
    parser.add_argument(
        "--no-venv", action="store_true", help="No crear entorno virtual"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Mostrar información detallada"
    )
    args = parser.parse_args()

    # Configurar nivel de logging verboso si se solicita
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Modo verboso activado")

    # Cargar configuración existente
    load_config_state()

    logger.info("=== Iniciando configuración de XTTS WebUI para entorno local ===")
    logger.info(
        f"Sistema operativo detectado: {platform.system()} {platform.release()}"
    )

    try:
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

        # Descarga de recursos si es necesario
        if args.force_download or (
            not args.skip_download and not config_state.get("models_downloaded", False)
        ):
            download_resources()
        elif args.skip_download:
            logger.info("Omitiendo descarga de modelos por parámetro --skip-download")
        elif config_state.get("models_downloaded", False):
            logger.info(
                "Modelos ya descargados según el registro. Use --force-download para descargar nuevamente."
            )

        # Aplicar parches de compatibilidad
        apply_compatibility_patch()

        # Crear script de lanzamiento
        launcher_path = create_launcher_script(python_exe)

        # Guardar estado de configuración
        save_config_state()

        # Instrucciones finales
        logger.info("\n=== Instalación completada con éxito ===")

        if launcher_path:
            logger.info(
                f"Para iniciar XTTS WebUI, ejecute: {python_exe} {launcher_path}"
            )
        else:
            logger.info(
                f"Para iniciar XTTS WebUI, navegue a {XTTS_DIR} y ejecute: {python_exe} xtts_demo.py --port 7860"
            )

        logger.info("La interfaz estará disponible en http://localhost:7860")
        logger.info(
            "Presione Ctrl+C en la terminal para detener la aplicación cuando desee cerrarla"
        )

        return 0
    except KeyboardInterrupt:
        logger.info("\n⚠️ Instalación interrumpida por el usuario")
        return 1
    except Exception as e:
        logger.error(f"\n❌ Error inesperado durante la instalación: {e}")
        logger.error(traceback.format_exc())

        # Registrar el error en el estado
        config_state["error_log"].append(
            {
                "timestamp": time.time(),
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
        )
        save_config_state()

        return 1


if __name__ == "__main__":
    sys.exit(main())
