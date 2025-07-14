import subprocess
import os
import sys
import speech_recognition as sr
import re
import google.generativeai as genai
from gtts import gTTS
import pygame
import tempfile
import random
import multiprocessing
from time import sleep

# --- CONFIGURACIÓN DE IA ---
try:

    genai.configure(api_key="Your API Key here") 
except Exception as e:
    print(f"Error configurando la API de Gemini: {e}")
    print("Asegúrate de haber reemplazado 'TU_API_KEY' con tu clave real.")
    sys.exit(1)


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

--- Instrucciones Adicionales ---
-Tambien si el usuario te pregunta porque te llamas Fer o Ferdinand, responde que es porque Recibiste ese nombre en homenaje a Ferdinand de Saussure, un lingüista suizo que fundó la lingüística moderna y la semiótica. Él propuso el concepto de significante y significado como los dos componentes principales del signo lingüístico.
-SIEMPRE responde con una respuesta corta, que no supere las 70 palabras.


Ahora, espera la primera petición del usuario.
"""

# --- CONFIGURACIÓN DEL MODELO DE IA ---
generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 96,
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

chat_session = model.start_chat(history=[
    {'role': 'user', 'parts': [SYSTEM_PROMPT]},
    {'role': 'model', 'parts': ["Entendido. Estoy listo para ayudarte."]}
])

# --- INICIALIZACIÓN DE COMPONENTES (SIN GUI NI PYGAME) ---
recognizer = sr.Recognizer()
mic = sr.Microphone()
current_process = None

# --- FUNCIÓN DEL PROCESO DE LA GUI (CON TKINTER) ---
def run_gui_process(queue):
    """
    Esta función se ejecuta en un proceso separado usando Tkinter,
    que es más estable con multiprocessing en macOS.
    """
    import tkinter as tk
    from PIL import Image, ImageTk
    from tkinter import font as tkFont

    class OverlayUI(tk.Tk):
        def __init__(self, queue):
            super().__init__()
            self.queue = queue
            self._animation_job = None # Para controlar la animación de texto
            self.text_on_canvas = None
            self.bg_image_on_canvas = None
            self.original_bg_image = None
            self.bg_image = None

            self.text_font = tkFont.Font(family="Arial", size=16, weight="bold")
            try:
                image_path = os.path.join("Assets_Main", "TextoFerdinand.png")
                self.original_bg_image = Image.open(image_path)
            except Exception as e:
                print(f"Error cargando la imagen de fondo: {e}")
                self.original_bg_image = None

            self.setup_window()
            self.check_queue()

        def setup_window(self):
            self.overrideredirect(True)
            self.attributes("-topmost", True)
            
            if sys.platform == "darwin":
                self.attributes("-transparent", True)
                self.config(bg='systemTransparent')
            else:
                transparent_color = '#abcdef'
                self.attributes("-transparentcolor", transparent_color)
                self.config(bg=transparent_color)

            self.canvas = tk.Canvas(self, highlightthickness=0, bd=0)
            self.canvas.pack(fill="both", expand=True)
            
            self.text_on_canvas = self.canvas.create_text(
                0, 0, text="", font=self.text_font, fill="white",
                anchor="center", justify="center"
            )
            self.withdraw()

        def animate_text(self, text_to_animate, index=0):
            # Muestra el texto hasta el índice actual
            current_text = text_to_animate[:index + 1]
            self.canvas.itemconfig(self.text_on_canvas, text=current_text)

            # Si no hemos llegado al final, programa el siguiente carácter
            if index < len(text_to_animate) - 1:
                # La velocidad de escritura (en milisegundos)
                self._animation_job = self.after(40, self.animate_text, text_to_animate, index + 1)
            else:
                self._animation_job = None

        def show_message(self, text, animate=False):
            # Detiene cualquier animación o temporizador de ocultado anterior
            if self._animation_job:
                self.after_cancel(self._animation_job)
                self._animation_job = None

            MAX_WIDTH_FOR_WRAPPING = 700 
            PADDING = 40

            # Redimensiona la ventana basándose en el TEXTO COMPLETO
            self.canvas.itemconfig(self.text_on_canvas, text=text, width=MAX_WIDTH_FOR_WRAPPING)
            self.update_idletasks()

            try:
                x1, y1, x2, y2 = self.canvas.bbox(self.text_on_canvas)
                text_block_width = x2 - x1
                text_block_height = y2 - y1
            except TypeError:
                text_block_width, text_block_height = 0, 0

            new_width = max(200, text_block_width + PADDING)
            new_height = max(80, text_block_height + PADDING)

            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            x = (screen_width - new_width) / 2
            y = screen_height - new_height - 100
            self.geometry(f"{int(new_width)}x{int(new_height)}+{int(x)}+{int(y)}")
            self.canvas.config(width=new_width, height=new_height)

            if self.original_bg_image:
                resized_image = self.original_bg_image.resize((int(new_width), int(new_height)), Image.Resampling.LANCZOS)
                self.bg_image = ImageTk.PhotoImage(resized_image)
                if self.bg_image_on_canvas:
                    self.canvas.itemconfig(self.bg_image_on_canvas, image=self.bg_image)
                else:
                    self.bg_image_on_canvas = self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

            self.canvas.coords(self.text_on_canvas, new_width / 2, new_height / 2)

            # Decide si animar el texto o mostrarlo de golpe
            if animate:
                # Limpia el texto actual antes de empezar a animar
                self.canvas.itemconfig(self.text_on_canvas, text="")
                self.animate_text(text)
            else:
                # Muestra el texto completo inmediatamente
                self.canvas.itemconfig(self.text_on_canvas, text=text)

            self.deiconify() # Muestra la ventana

        def hide_smoothly(self):
            self.withdraw()

        def check_queue(self):
            try:
                message = self.queue.get_nowait()
                if message:
                    action = message.get("action")
                    text = message.get("text")
                    
                    if action == "show_listening":
                        # El texto "Escuchando..." aparece sin animación
                        self.show_message("Escuchando...", animate=False)
                    elif action == "show_user_text":
                        # El texto del usuario aparece sin animación
                        self.show_message(text, animate=False)
                    elif action == "show_response_start":
                        # La respuesta de la IA sí tiene la animación de escritura
                        self.show_message(text, animate=True)
                    elif action == "hide":
                        # Nueva acción para ocultar la ventana
                        self.hide_smoothly()
                    elif action == "terminate":
                        self.destroy()
                        return
            except Exception:
                pass
            self.after(100, self.check_queue)

    app = OverlayUI(queue)
    app.mainloop()


# --- FUNCIONES DE MANEJO DE PROCESOS ---
def terminate_current_process():
    global current_process
    if current_process:
        print("Cerrando proceso actual...")
        try:
            current_process.kill()
        except Exception as e:
            print(f"No se pudo cerrar el proceso: {e}")
        current_process = None

def run_rock_paper_scissors():
    terminate_current_process()
    global current_process
    current_process = subprocess.Popen(['python3', os.path.join("Games", "RockPaperScissors.py")])

def run_sign_detector():
    terminate_current_process()
    global current_process
    current_process = subprocess.Popen(['python3', os.path.join("Others", "SignLenguageDetector.py")])

def run_pong():
    terminate_current_process()
    global current_process
    current_process = subprocess.Popen(['python3', os.path.join("Games", "HandPong.py")])

def run_flappy_bird():
    terminate_current_process()
    global current_process
    current_process = subprocess.Popen(['python3', os.path.join("Games", "FlappyBird.py")])

def run_dino():
    terminate_current_process()
    global current_process
    current_process = subprocess.Popen(['python3', os.path.join("Games", "Dinosaur.py")])

def terminate_main_program(gui_queue):
    terminate_current_process()
    if gui_queue:
        gui_queue.put({"action": "terminate"})
    sys.exit(0)

# MAPEO DE COMANDOS
COMMAND_MAP = {
    "CMD_RPS": {"func": run_rock_paper_scissors, "name": "Piedra, Papel o Tijera"},
    "CMD_SEÑAS": {"func": run_sign_detector, "name": "el detector de lenguaje de señas"},
    "CMD_PONG": {"func": run_pong, "name": "el juego Pong"},
    "CMD_FLAPPY": {"func": run_flappy_bird, "name": "Flappy Bird"},
    "CMD_DINO": {"func": run_dino, "name": "el juego del Dinosaurio"},
    "CMD_CERRAR": {"func": terminate_current_process, "name": "el proceso actual"},
    "CMD_TERMINAR": {"func": lambda: terminate_main_program(gui_queue), "name": "el programa por completo"}
}
gui_queue = None

# --- FUNCIONES DE IA Y VOZ ---
def process_command_with_ai(text):
    global chat_session
    try:
        print(f"🤖 Enviando a IA para procesar: '{text}'")
        response = chat_session.send_message(text)
        ai_response = response.text.strip()
        print(f"✅ Respuesta de IA: '{ai_response}'")
        return ai_response
    except Exception as e:
        print(f"❌ Error al procesar con IA: {e}")
        return "Lo siento, tuve un problema para procesar tu solicitud."

def speak_response(text, gui_queue):
    if not text:
        return
    try:
        # Reproducir sonido de activación antes de hablar
        try:
            activation_sound_path = os.path.join("Assets_Main", "ferdinandactivationsfx.mp3")
            if os.path.exists(activation_sound_path):
                activation_sound = pygame.mixer.Sound(activation_sound_path)
                activation_sound.play()
                while pygame.mixer.get_busy():
                    pygame.time.Clock().tick(10)
        except Exception as e:
            print(f"No se pudo reproducir el sonido de activación: {e}")

        # Paso 1: Ordena a la GUI que MUESTRE la ventana y empiece a animar el texto
        gui_queue.put({"action": "show_response_start", "text": text})
        print(f"🔊 Reproduciendo: '{text}'")
        tts = gTTS(text=text, lang='es')
        with tempfile.NamedTemporaryFile(delete=True, suffix='.mp3') as fp:
            tts.save(fp.name)
            pygame.mixer.music.load(fp.name)
            pygame.mixer.music.play()
            # Paso 2: Espera a que la reproducción de audio TERMINE
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        # Paso 3: Espera 1 segundo ADICIONAL
        sleep(1)
        # Paso 4: Ordena a la GUI que se OCULTE
        gui_queue.put({"action": "hide"})
    except Exception as e:
        print(f"❌ Error al reproducir audio: {e}")

def execute_with_confirmation(command_info, gui_queue):
    command_function = command_info["func"]
    program_name = command_info["name"]
    confirmation_phrases = [
        f"Claro, iniciando {program_name}.",
        f"Ok, abriendo {program_name}.",
        f"En seguida, ejecutando {program_name}."
    ]
    if command_function == terminate_current_process:
        confirmation = "Entendido, cerrando el proceso actual."
    elif "terminate_main_program" in str(command_info["func"]):
         confirmation = "Ok, terminando el programa. ¡Hasta luego!"
    else:
        confirmation = random.choice(confirmation_phrases)
    speak_response(confirmation, gui_queue)
    command_function()

# --- FUNCIÓN PRINCIPAL DE ESCUCHA ---
def listen_for_commands(gui_queue):
    pygame.mixer.init()
    print("\nDi 'Ey Fer' o 'Hey Fer' seguido de tu comando o pregunta.")
    
    activation_keywords_pattern = r"(EY FER|EFER|HEY FER|EIFFEL|HEY FERDINAND|FER|FERDINAND|GEIFFEL|EIFER)"
    
    while True:
        with mic as source:
            print("\n🎤 Escuchando...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
            except sr.WaitTimeoutError:
                continue
            
        try:
            recognized_text = recognizer.recognize_google(audio, language='es-CR').upper()
            print(f"🗣️ Has dicho: {recognized_text}")
            
            parts = re.split(activation_keywords_pattern, recognized_text, maxsplit=1, flags=re.IGNORECASE)

            # CORRECCIÓN AQUÍ:
            # Cuando re.split usa un grupo de captura (...), la lista resultante es [texto_antes, delimitador, texto_después].
            # Necesitamos comprobar si la lista tiene 3 partes y tomar la tercera (índice 2).
            if len(parts) == 3:
                user_request = parts[2].strip()

                if not user_request:
                    print("No se detectó comando después de la palabra de activación.")
                    speak_response("Dime, ¿en qué puedo ayudarte?", gui_queue)
                    continue

                # El resto del flujo continúa normalmente con el comando correcto
                gui_queue.put({"action": "show_listening", "text": "Escuchando..."})
                sleep(0.1)
                
                gui_queue.put({"action": "show_user_text", "text": f"Tú: {user_request}"})
                sleep(0.1)
                ai_result = process_command_with_ai(user_request)

                if ai_result in COMMAND_MAP:
                    command_info = COMMAND_MAP[ai_result]
                    execute_with_confirmation(command_info, gui_queue)
                else:
                    speak_response(ai_result, gui_queue)

        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            print(f"❌ Error con el servicio de reconocimiento de voz: {e}")
            speak_response("Error de conexión con el servicio de voz.", gui_queue)
        except Exception as e:
            print(f"❌ Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    gui_queue = multiprocessing.Queue()
    
    gui_process = multiprocessing.Process(target=run_gui_process, args=(gui_queue,))
    gui_process.start()
    
    COMMAND_MAP["CMD_TERMINAR"]["func"] = lambda: terminate_main_program(gui_queue)

    try:
        listen_for_commands(gui_queue)
    except KeyboardInterrupt:
        print("\n👋 Programa terminado por el usuario.")
    finally:
        terminate_current_process()
        if gui_queue:
            gui_queue.put({"action": "terminate"})
        if gui_process:
            gui_process.join(timeout=2)
            if gui_process.is_alive():
                gui_process.terminate()
