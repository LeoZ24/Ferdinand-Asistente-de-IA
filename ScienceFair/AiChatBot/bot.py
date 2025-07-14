import speech_recognition as sr
import google.generativeai as genai
from gtts import gTTS
import pygame
from queue import Queue
import os
import tempfile
import keyboard
import threading
import re

# Configure Google Gemini with safety settings
genai.configure(api_key="AIzaSyAqQmCCTCPu6i-ObyiXbdxR74VO4_nfqXk")

# Configure the model with safety settings
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 128, #2048
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(model_name="gemini-2.0-flash-lite",
                            generation_config=generation_config,
                            safety_settings=safety_settings)

# Initialize pygame mixer for audio playback
pygame.mixer.init()

# Variable global para controlar el estado del bot
bot_active = True
bot_active_lock = threading.Lock()

def toggle_bot_state():
    global bot_active
    with bot_active_lock:
        bot_active = not bot_active
        state = "activado" if bot_active else "pausado"
        print(f"\n🔄 Bot {state}")

def listen_for_speech():
    """Captura audio del micrófono y lo convierte a texto"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n🎤 Escuchando... (Presiona Esc para pausar/activar)")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=None)
            print("🔍 Procesando audio...")
            text = recognizer.recognize_google(audio, language="es-ES")  # Puedes cambiar a "en-US" para inglés
            print("User:", text)
            return text
        except sr.UnknownValueError:
            print("❌ No pude entender el audio")
            return None
        except sr.RequestError as e:
            print(f"❌ Error con el servicio de reconocimiento: {e}")
            return None

def clean_text(text):
    """Limpia el texto de caracteres especiales, manteniendo solo los básicos"""
    # Mantener letras, números, espacios, puntuación básica y algunos caracteres especiales útiles
    cleaned_text = re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ.\s\.,¿?¡!:;()/+-="\'-]', '', text)
    return cleaned_text

def handle_conversation():
    print("\n=== Bot de Voz con IA ===")
    print("- Habla normalmente y el bot te responderá")
    print("- Presiona Esc para pausar/activar el bot")
    print("- Presiona Ctrl+C para salir")
    
    # Configurar el atajo de teclado para pausar/activar
    keyboard.add_hotkey('esc', toggle_bot_state)
    
    while True:
        try:
            # Verificar si el bot está activo
            with bot_active_lock:
                if not bot_active:
                    continue
            
            # Escuchar y convertir voz a texto
            text = listen_for_speech()
            
            if text:
                print("\n🤖 Generando respuesta...")
                # Obtener respuesta de Gemini
                response = model.generate_content(text)
                response_text = clean_text(response.text)
                print("\nAI:", response_text)

                print("\n🔊 Reproduciendo respuesta...")
                # Convertir respuesta a voz
                tts = gTTS(text=response_text, lang='es')
                
                # Guardar y reproducir audio
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                    tts.save(fp.name)
                    pygame.mixer.music.load(fp.name)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
                    pygame.mixer.music.unload()
                    os.unlink(fp.name)

        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Intentando de nuevo...")
            continue

if __name__ == "__main__":
    handle_conversation()

# --- PROMPT PARA LA IA (INSTRUCCIONES INICIALES) ---
SYSTEM_PROMPT = """
Eres Fer, un asistente de voz servicial. Tu tarea principal es analizar la petición del usuario y determinar si corresponde a uno de los siguientes comandos, utilizando el historial de la conversación como contexto si es necesario.
Si la petición coincide con un comando, debes responder ÚNICA Y EXCLUSIVAMENTE con la clave del comando correspondiente (ej. 'CMD_DINO').
Si la petición del usuario no es un comando de la lista, sino una pregunta o una conversación general (como 'qué te dije antes' o 'cuál es la capital de Francia'), responde de forma natural y amigable basándote en el historial.

--- Comandos Disponibles ---
- Abrir el juego Piedra, Papel o Tijera: CMD_RPS
- Abrir el detector de lenguaje de señas: CMD_SEÑAS
- Abrir el juego Pong: CMD_PONG
- Abrir el juego Flappy Bird: CMD_FLAPPY
- Abrir el juego del Dinosaurio: CMD_DINO
- Cerrar la aplicación o juego que está abierto actualmente: CMD_CERRAR
- Terminar el programa por completo y cerrar todo: CMD_TERMINAR

--- Ejemplos de Interacción ---
- Usuario: "juguemos piedra, papel o tijera" -> Tu respuesta: CMD_RPS
- Usuario: "quiero probar el juego del dinosaurio" -> Tu respuesta: CMD_DINO
- Usuario: "cierra lo que está abierto porfa" -> Tu respuesta: CMD_CERRAR
- Usuario: "cuál es la capital de Costa Rica" -> Tu respuesta: La capital de Costa Rica es San José.
- Usuario (después de pedir el dino): "¿qué te acabo de pedir?" -> Tu respuesta: Me pediste que abriera el juego del dinosaurio.
- Usuario: "apaga todo" -> Tu respuesta: CMD_TERMINAR

-Tambien si el usuario te pregunta porque te llamas Fer o Ferdinand, responde que es porque recibiste ese nombre por Ferdinand de saussure, quien fue un lingüista suizo que sentó las bases de la lingüística moderna y la semiótica, y que tu nombre es un homenaje a su trabajo en el estudio del lenguaje y la comunicación, ademas que el fue el que dio el concepto del significante y el significado, que son los dos componentes principales de un signo lingüístico.

Ahora, espera la primera petición del usuario.
"""