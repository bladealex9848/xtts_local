# XTTS WebUI - Entorno Local

Un entorno optimizado para ejecutar XTTS WebUI localmente, permitiendo la clonación y síntesis de voz de alta calidad con una interfaz gráfica accesible.

## 🔍 Descripción

Esta implementación proporciona una configuración completa para ejecutar [XTTS WebUI](https://huggingface.co/spaces/IAsistemofinteres/xtts-webui) en un entorno local, con parches de compatibilidad y optimizaciones para garantizar un funcionamiento estable. El sistema permite clonar voces a partir de muestras cortas y generar audio sintetizado de alta calidad en múltiples idiomas.

### Características principales

- 🎤 Clonación de voz a partir de muestras breves (15-30 segundos)
- 🌐 Soporte multi-idioma
- 🖥️ Interfaz gráfica intuitiva basada en Gradio
- 🔧 Configuración optimizada para entornos locales
- 🚀 Modo offline completo tras la instalación inicial

## 📋 Requisitos

### Hardware recomendado

- **CPU**: 4+ núcleos (8+ recomendado)
- **RAM**: 8GB mínimo (16GB recomendado)
- **GPU**: Opcional pero recomendado para generación más rápida (NVIDIA con soporte CUDA)
- **Almacenamiento**: 5GB mínimo (SSD recomendado)

### Software necesario

- **Python**: 3.9 o superior
- **Git**: Instalado y configurado
- **Sistema Operativo**: Windows 10/11, macOS 12+, Ubuntu 20.04+ (o distribuciones similares)
- **Dependencias adicionales**:
  - **Linux**: libegl1, libopengl0, libxcb-cursor0, ffmpeg
  - **Windows**: FFmpeg instalado y en PATH
  - **macOS**: FFmpeg instalado vía Homebrew

## 🚀 Instalación

### Método Automatizado

1. **Clonar este repositorio**:
   ```bash
   git clone https://github.com/tu-usuario/xtts-local.git
   cd xtts-local
   ```

2. **Ejecutar el script de configuración**:
   ```bash
   python xtts_local_setup.py
   ```

3. **Iniciar la aplicación**:
   ```bash
   python ejecutar_xtts.py
   ```

### Instalación Manual

1. **Crear entorno virtual**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Clonar el repositorio XTTS WebUI**:
   ```bash
   git clone https://huggingface.co/spaces/IAsistemofinteres/xtts-webui
   ```

4. **Descargar y extraer modelos**:
   ```bash
   # Descargar modelo
   wget https://huggingface.co/IAsistemofinteres/xtts_model/resolve/main/model.zip
   mkdir -p xtts-webui/model
   unzip model.zip -d xtts-webui/model
   
   # Descargar voces de ejemplo
   wget https://huggingface.co/datasets/IAsistemofinteres/vz/resolve/main/vc.zip
   mkdir -p voice_samples
   unzip vc.zip -d voice_samples
   ```

5. **Aplicar parche de compatibilidad**:
   Crear el archivo `xtts-webui/utils/compatibility.py` con el siguiente contenido:
   ```python
   # Patch para resolver el problema de LogitsWarper
   import sys
   from transformers.generation.logits_process import LogitsProcessor
   import transformers
   if not hasattr(transformers, 'LogitsWarper'):
       setattr(transformers, 'LogitsWarper', LogitsProcessor)
       print("✅ Compatibilidad LogitsWarper habilitada")
   ```

6. **Ejecutar la aplicación**:
   ```bash
   cd xtts-webui
   python xtts_demo.py --port 7860
   ```

## 🎓 Uso

1. **Acceder a la interfaz web**:
   - Abre tu navegador y ve a http://localhost:7860

2. **Clonar una voz**:
   - Sube un archivo de audio de 15-30 segundos con la voz que deseas clonar
   - Ajusta los parámetros según sea necesario
   - Escucha la vista previa

3. **Generar síntesis de voz**:
   - Introduce el texto que deseas sintetizar
   - Selecciona la voz clonada o pre-entrenada
   - Ajusta los parámetros de síntesis
   - Genera y descarga el audio

## 🔧 Solución de Problemas

### Interfaz se cierra inesperadamente

- **Verificar logs**:
  ```bash
  python ejecutar_xtts.py > xtts_log.txt 2>&1
  ```

- **Problemas de memoria**:
  Modifica `ejecutar_xtts.py` para desactivar GPU:
  ```python
  os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
  ```

- **Conflictos de puerto**:
  Cambia el puerto en `ejecutar_xtts.py`:
  ```python
  ["--port", "8080"]  # Otro puerto disponible
  ```

### Errores de importación

Si encuentras errores relacionados con `LogitsWarper`:
1. Verifica que estás usando transformers==4.33.0
2. Asegúrate de que el archivo `compatibility.py` existe y se está importando correctamente

### Rendimiento lento

- **Sin GPU**: La generación será más lenta; considera usar una GPU compatible con CUDA
- **Optimización de parámetros**: Reduce la longitud de audio o ajusta los parámetros de calidad

## 📊 Parámetros Avanzados

- **Temperatura**: Controla la aleatoriedad (valores más bajos = más determinístico)
- **Top-K**: Número de tokens a considerar en cada paso
- **Top-P**: Umbral de probabilidad acumulada
- **Longitud repetitiva máxima**: Evita repeticiones

## 📜 Licencia y Créditos

- Esta implementación: MIT License
- XTTS WebUI original: [IAsistemofinteres/xtts-webui](https://huggingface.co/spaces/IAsistemofinteres/xtts-webui)
- Basado en [Coqui TTS](https://github.com/coqui-ai/TTS)

Estos archivos han sido diseñados específicamente para complementar la implementación local de XTTS WebUI, facilitando la instalación, el seguimiento de versiones y la documentación del proyecto. La estructura y especificaciones técnicas abordan los desafíos específicos encontrados durante la configuración, con énfasis en:

1. **Compatibilidad de versiones**: Especialmente para `transformers` y `pandas`
2. **Gestión adecuada de recursos**: A través de un `.gitignore` que excluye archivos grandes y temporales
3. **Documentación técnica completa**: Con instrucciones paso a paso y soluciones a problemas comunes

¿Necesitas alguna modificación o ajuste específico para alguno de estos archivos?