#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Launcher for XTTS WebUI
Creado automáticamente por xtts_local_setup.py
"""
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

# Variables globales
process = None

def signal_handler(sig, frame):
    """Manejador de señal para SIGINT (Ctrl+C)"""
    logger.info("\n⚠️ Recibida señal de interrupción. Finalizando de forma segura...")
    if process:
        process.terminate()
        try:
            process.wait(timeout=5)
            logger.info("Proceso finalizado correctamente")
        except subprocess.TimeoutExpired:
            logger.warning("El proceso no terminó tras 5 segundos, forzando finalización...")
            process.kill()
    sys.exit(0)

def apply_compatibility_patch():
    """Aplica el parche de compatibilidad de manera programática"""
    try:
        import transformers
        from transformers.generation.logits_process import LogitsProcessor
        if not hasattr(transformers, 'LogitsWarper'):
            setattr(transformers, 'LogitsWarper', LogitsProcessor)
            logger.info("✓ Parche dinámico aplicado correctamente")
        return True
    except Exception as e:
        logger.error(f"❌ Error al aplicar parche dinámico: {e}")
        return False

def main():
    """Función principal para ejecutar XTTS WebUI"""
    global process
    
    # Registrar manejador de señal
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Cambiar al directorio del proyecto
        project_dir = "/Volumes/NVMe1TB/GitHub/xtts_local/xtts-webui"
        logger.info(f"Cambiando al directorio: {project_dir}")
        os.chdir(project_dir)
        
        # Agregar directorio al path
        sys.path.insert(0, project_dir)
        
        # Importar o aplicar parche de compatibilidad
        compatibility_loaded = False
        try:
            compatibility_path = os.path.join(project_dir, "utils")
            sys.path.insert(0, compatibility_path)
            # Importación específica en lugar de import *
            import compatibility
            logger.info("✓ Módulo de compatibilidad cargado correctamente")
            compatibility_loaded = True
        except ImportError as e:
            logger.warning(f"⚠️ No se pudo cargar el módulo de compatibilidad: {e}")
            logger.info("Aplicando parche dinámico...")
            compatibility_loaded = apply_compatibility_patch()
        
        if not compatibility_loaded:
            logger.warning("No se pudo aplicar el parche de compatibilidad")
            logger.warning("Algunas funcionalidades podrían no estar disponibles")
        
        # Verificar modelo
        model_config = os.path.join(project_dir, "model", "config.json")
        if not os.path.exists(model_config):
            logger.error(f"❌ No se encontró el archivo de configuración del modelo en {model_config}")
            logger.error("Ejecute xtts_local_setup.py para descargar los modelos necesarios")
            sys.exit(1)
        
        # Configurar variables de entorno
        os.environ['PYTHONUNBUFFERED'] = '1'
        os.environ['GRADIO_ANALYTICS_ENABLED'] = 'False'
        
        # Ejecutar la interfaz
        logger.info("\n🚀 Iniciando XTTS WebUI...")
        logger.info("⏳ La inicialización puede tomar hasta 2 minutos en la primera ejecución")
        logger.info("🔗 La interfaz estará disponible en http://localhost:7860 cuando termine de cargar")
        logger.info("-------------------------------------------------------------------")
        
        # Buscar el script principal
        main_script = "app.py"
        if not os.path.exists(os.path.join(project_dir, main_script)):
            logger.warning(f"❌ No se encontró el archivo {main_script}")
            
            # Buscar alternativas
            script_candidates = [
                "app.py", "webui.py", "main.py", "server.py", "run.py", 
                "gradio_app.py", "xtts_app.py", "xtts_demo.py"
            ]
            
            for candidate in script_candidates:
                if os.path.exists(os.path.join(project_dir, candidate)):
                    main_script = candidate
                    logger.info(f"✓ Usando archivo alternativo: {main_script}")
                    break
            else:
                # Si no encuentra ninguno, listar todos los archivos Python
                py_files = [f for f in os.listdir(project_dir) if f.endswith('.py')]
                if py_files:
                    main_script = py_files[0]
                    logger.info(f"✓ Usando primer archivo Python disponible: {main_script}")
                else:
                    logger.error("❌ No se encontraron archivos Python en el directorio")
                    sys.exit(1)
        
        # Usar subprocess para mantener la interfaz abierta
        python_exe = "/Volumes/NVMe1TB/GitHub/xtts_local/venv/bin/python"
        cmd = [python_exe, main_script, "--port", "7860"]
        logger.debug(f"Ejecutando comando: {' '.join(cmd)}")
        
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
                logger.info("\n✅ Interfaz iniciada correctamente")
            if "Error" in line or "ERROR" in line or "error" in line:
                logger.warning(f"⚠️ Posible error detectado: {line.strip()}")
        
        # Esperar a que el proceso termine
        return_code = process.wait()
        if return_code != 0:
            logger.error(f"❌ El proceso terminó con código: {return_code}")
        else:
            logger.info("Proceso finalizado correctamente")
    
    except KeyboardInterrupt:
        logger.info("\n⚠️ Operación interrumpida por el usuario")
        if process:
            logger.info("Finalizando proceso...")
            process.terminate()
            process.wait()
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        logger.error(traceback.format_exc())
        if process:
            process.terminate()
            process.wait()
        sys.exit(1)

if __name__ == "__main__":
    main()
