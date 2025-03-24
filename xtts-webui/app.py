#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XTTS WebUI - Punto de entrada personalizado
"""
import os
import sys
import gradio as gr
from TTS.api import TTS

# Configuración básica
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model")
VOICE_SAMPLES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "voice_samples")

# Verificación de modelo
if not os.path.exists(os.path.join(MODEL_PATH, "config.json")):
    print("ERROR: No se encontró el modelo XTTS. Asegúrese de que se ha descargado correctamente.")
    sys.exit(1)

def text_to_speech(text, voice_sample=None, language="es", speed=1.0):
    """Función de síntesis de voz"""
    try:
        # Inicializar el modelo TTS
        tts = TTS(model_path=MODEL_PATH)
        
        # Configurar salida
        output_file = os.path.join(os.path.dirname(__file__), "output.wav")
        
        # Generar audio
        if voice_sample:
            tts.tts_with_xtts_to_file(
                text=text,
                speaker_wav=voice_sample,
                language=language,
                speed=speed,
                file_path=output_file
            )
        else:
            tts.tts_to_file(text=text, file_path=output_file)
        
        return output_file
    except Exception as e:
        print(f"Error en síntesis: {e}")
        return None

# Interfaz Gradio
def create_interface():
    with gr.Blocks(title="XTTS Web UI") as demo:
        gr.Markdown("# XTTS Web UI - Sistema de Clonación de Voz")
        
        with gr.Tab("Síntesis de Voz"):
            with gr.Row():
                with gr.Column():
                    text_input = gr.TextArea(label="Texto a sintetizar", placeholder="Ingrese el texto que desea convertir a voz...")
                    voice_sample = gr.Audio(label="Muestra de voz (opcional)", type="filepath")
                    language = gr.Dropdown(label="Idioma", choices=["es", "en", "fr", "de", "it", "pt"], value="es")
                    speed = gr.Slider(label="Velocidad", minimum=0.5, maximum=2.0, value=1.0, step=0.1)
                    submit_btn = gr.Button("Generar Voz", variant="primary")
                
                with gr.Column():
                    output_audio = gr.Audio(label="Voz Generada")
        
        # Conectar eventos
        submit_btn.click(
            fn=text_to_speech,
            inputs=[text_input, voice_sample, language, speed],
            outputs=[output_audio]
        )
    
    return demo

# Iniciar la aplicación
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="XTTS WebUI")
    parser.add_argument("--share", action="store_true", help="Compartir la interfaz públicamente")
    parser.add_argument("--port", type=int, default=7860, help="Puerto para la interfaz web")
    args = parser.parse_args()
    
    demo = create_interface()
    demo.launch(share=args.share, server_port=args.port)
