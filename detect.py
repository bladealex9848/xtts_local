#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XTTS WebUI Detector - Herramienta para identificar el punto de entrada de la aplicación
"""
import os
import sys
import glob

def find_app_entry_point(repo_dir):
    """Identifica el punto de entrada de la aplicación Gradio"""
    # Candidatos comunes
    candidates = ["app.py", "webui.py", "main.py", "server.py", "run.py", "xtts_app.py"]
    
    for candidate in candidates:
        full_path = os.path.join(repo_dir, candidate)
        if os.path.exists(full_path):
            print(f"Punto de entrada encontrado: {candidate}")
            return candidate
    
    # Búsqueda en contenido
    python_files = glob.glob(os.path.join(repo_dir, "*.py"))
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if "gradio" in content and ("app =" in content or "demo =" in content):
                    filename = os.path.basename(py_file)
                    print(f"Probable punto de entrada: {filename}")
                    return filename
        except Exception as e:
            print(f"Error al leer {py_file}: {e}")
    
    # Listar todos los archivos Python disponibles
    print("No se encontró un punto de entrada claro. Archivos Python disponibles:")
    for py_file in python_files:
        print(f"  - {os.path.basename(py_file)}")
    
    return None

if __name__ == "__main__":
    repo_dir = "/Volumes/NVMe1TB/GitHub/xtts_local/xtts-webui"
    find_app_entry_point(repo_dir)