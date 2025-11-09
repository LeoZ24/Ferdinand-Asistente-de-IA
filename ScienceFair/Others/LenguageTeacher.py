import tkinter as tk
from tkinter import ttk
import random
import speech_recognition as sr
from gtts import gTTS
import os
import threading
import subprocess
import uuid

# Intento importar playsound; si no está disponible usamos afplay (macOS)
try:
    from playsound import playsound  # type: ignore
    _HAS_PLAYSOUND = True
except Exception:
    playsound = None
    _HAS_PLAYSOUND = False


class ProfesorIdiomasApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Profesor de Idiomas")
        # Pantalla completa si es posible
        try:
            self.root.attributes('-fullscreen', True)
        except Exception:
            try:
                self.root.state('zoomed')
            except Exception:
                pass

        # Idiomas y vocabulario (practicar desde inglés hacia el idioma elegido)
        self.languages = {
            "Español": "es",
            "Francés": "fr",
            "Alemán": "de",
            "Italiano": "it",
            "Portugués": "pt"
        }

        self.words = {
            "Español": {
                "hello": "hola",
                "goodbye": "adiós",
                "cat": "gato",
                "dog": "perro",
                "house": "casa",
                "food": "comida",
                "water": "agua",
                "thank you": "gracias",
                "please": "por favor",
                "excuse me": "disculpe"
            },
            "Francés": {
                "hello": "bonjour",
                "goodbye": "au revoir",
                "cat": "chat",
                "dog": "chien",
                "house": "maison",
                "food": "nourriture",
                "water": "eau",
                "thank you": "merci",
                "please": "s'il vous plaît",
                "excuse me": "excusez-moi"
            },
            "Alemán": {
                "hello": "hallo",
                "goodbye": "auf wiedersehen",
                "cat": "katze",
                "dog": "hund",
                "house": "haus",
                "food": "essen",
                "water": "wasser",
                "thank you": "danke",
                "please": "bitte",
                "excuse me": "entschuldigen sie"
            },
            "Italiano": {
                "hello": "ciao",
                "goodbye": "arrivederci",
                "cat": "gatto",
                "dog": "cane",
                "house": "casa",
                "food": "cibo",
                "water": "acqua",
                "thank you": "grazie",
                "please": "per favore",
                "excuse me": "scusi"
            },
            "Portugués": {
                "hello": "olá",
                "goodbye": "adeus",
                "cat": "gato",
                "dog": "cachorro",
                "house": "casa",
                "food": "comida",
                "water": "água",
                "thank you": "obrigado",
                "please": "por favor",
                "excuse me": "com licença"
            }
        }

        # Estado
        self.current_language = "Español"
        self.current_word = ""
        self.score = 0
        self.streak = 0
        self.mode = "Traducir"  # "Traducir" o "Escribir"

        # Colores y UI
        self.bg_color = "#f0fbf3"
        self.card_color = "#ffffff"
        self.accent = "#2fbf71"

        self._build_ui()
        self._next_word()

    def _build_ui(self):
        self.root.configure(bg=self.bg_color)
        # Fuente grande por defecto
        default_font = ("Helvetica", 12)
        self.root.option_add("*Font", default_font)

        self.container = ttk.Frame(self.root, padding=24)
        self.container.pack(fill=tk.BOTH, expand=True)

        top = ttk.Frame(self.container)
        top.pack(fill=tk.X, pady=(0, 20))

        title = ttk.Label(top, text="Profesor de Idiomas", font=("Helvetica", 30, "bold"), foreground=self.accent)
        title.pack(side=tk.LEFT)

        lang_frame = ttk.Frame(top)
        lang_frame.pack(side=tk.RIGHT)
        ttk.Label(lang_frame, text="Idioma:", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=(0, 8))
        self.lang_var = tk.StringVar(value=self.current_language)
        self.lang_menu = ttk.OptionMenu(lang_frame, self.lang_var, self.current_language, *self.languages.keys(), command=self._change_language)
        self.lang_menu.pack(side=tk.LEFT)

        ttk.Label(lang_frame, text="Modo:", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=(12, 8))
        self.mode_var = tk.StringVar(value=self.mode)
        self.mode_menu = ttk.OptionMenu(lang_frame, self.mode_var, self.mode, "Traducir", "Escribir", command=self._change_mode)
        self.mode_menu.pack(side=tk.LEFT)

        center = ttk.Frame(self.container)
        center.pack(fill=tk.BOTH, expand=True)

        # Tarjeta central con sombra simulada
        shadow = tk.Frame(center, bg="#cfead7")
        shadow.place(relx=0.5+0.01, rely=0.5+0.01, anchor=tk.CENTER, width=920, height=340)
        self.card = tk.Frame(center, bg=self.card_color, bd=0)
        self.card.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=900, height=320)

        self.prompt_label = tk.Label(self.card, text="", font=("Helvetica", 34, "bold"), bg=self.card_color, fg="#0b3d22", justify=tk.CENTER, wraplength=820)
        self.prompt_label.pack(pady=(0, 20))

        entry_frame = tk.Frame(self.card, bg=self.card_color)
        entry_frame.pack(fill=tk.X, padx=20)
        self.entry = tk.Entry(entry_frame, font=("Helvetica", 22), bd=2, relief=tk.GROOVE)
        self.entry.pack(fill=tk.X, ipady=8)
        # Enter ahora comprueba y avanza (la función _check_answer ya avanza tras un delay)
        self.entry.bind("<Return>", lambda e: self._check_answer())

        actions = tk.Frame(self.card, bg=self.card_color)
        actions.pack(pady=12)

        btn_cfg = {"bd": 0, "bg": self.accent, "fg": "#fff", "activebackground": "#27a35a", "padx": 12, "pady": 6}
        self.check_button = tk.Button(actions, text="Comprobar ✅", command=self._check_answer, **btn_cfg)
        self.check_button.grid(row=0, column=0, padx=8)

        self.voice_button = tk.Button(actions, text="Responder con voz 🎤", command=self._speak_answer, **btn_cfg)
        self.voice_button.grid(row=0, column=1, padx=8)

        self.pronounce_button = tk.Button(actions, text="Escuchar pronunciación 🔊", command=self._pronounce_word, **btn_cfg)
        self.pronounce_button.grid(row=0, column=2, padx=8)

        self.hint_button = tk.Button(actions, text="Pista 💡", command=self._hint, **btn_cfg)
        self.hint_button.grid(row=0, column=3, padx=8)

        self.feedback_label = tk.Label(self.card, text="", font=("Helvetica", 14), bg=self.card_color)
        self.feedback_label.pack(pady=(10, 0))

        # Barra de progreso simple
        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(self.card, orient='horizontal', mode='determinate', variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X, padx=20, pady=(6,0))

        bottom = tk.Frame(self.container, bg=self.bg_color)
        bottom.pack(fill=tk.X, pady=(20, 0))

        self.score_label = tk.Label(bottom, text=f"Puntuación: {self.score}", font=("Helvetica", 12), bg=self.bg_color)
        self.score_label.pack(side=tk.LEFT)

        self.streak_label = tk.Label(bottom, text=f"Racha: {self.streak}", font=("Helvetica", 12), bg=self.bg_color)
        self.streak_label.pack(side=tk.LEFT, padx=(10,0))

        self.next_button = tk.Button(bottom, text="Siguiente ➡️", command=self._next_word, bd=0, bg="#ddd", padx=10, pady=6)
        self.next_button.pack(side=tk.RIGHT)

        style = ttk.Style()
        style.theme_use('default')
        style.configure("TProgressbar", troughcolor='#e6f6ea', background=self.accent, thickness=10)
        title.configure(foreground=self.accent)

    def _change_language(self, lang):
        self.current_language = lang
        self.score = 0
        self.streak = 0
        self._update_score()
        self._next_word()

    def _change_mode(self, mode):
        self.mode = mode
        self._next_word()

    def _hint(self):
        # muestra una pista: primeras letras de la respuesta correcta
        if self.mode == "Traducir":
            correct_answer = self.words[self.current_language][self.current_word]
        else:
            correct_answer = self.current_word
        sz = max(1, len(correct_answer)//2)
        hint = correct_answer[:sz] + "..."
        # animación temporal
        self.feedback_label.config(text=f"Pista: {hint}", fg="#0066cc")
        self.root.after(2200, lambda: self.feedback_label.config(text=""))

    def _play_feedback_sound(self, kind: str):
        # kind: 'success'|'error'|'click'
        def _play():
            try:
                # Intentar usar sonidos locales si existen
                sounds = {
                    'success': "/System/Library/Sounds/Glass.aiff",
                    'error': "/System/Library/Sounds/Basso.aiff",
                    'click': "/System/Library/Sounds/Pop.aiff"
                }
                path = sounds.get(kind)
                if path and os.path.exists(path):
                    subprocess.run(["afplay", path])
                else:
                    # Fallback: usar say como sonido simple
                    if kind == 'success':
                        subprocess.run(["/usr/bin/say", "Correcto"])
                    elif kind == 'error':
                        subprocess.run(["/usr/bin/say", "Incorrecto"])
            except Exception:
                pass

        threading.Thread(target=_play, daemon=True).start()

    def _next_word(self):
        # Elegir palabra (clave en inglés). Mostramos según el modo y el idioma seleccionado
        self.current_word = random.choice(list(self.words[self.current_language].keys()))
        if self.mode == "Traducir":
            # mostramos la palabra en inglés y pedimos la traducción
            prompt_text = f"Traduce al {self.current_language}:\n\n{self.current_word}"
            self.prompt_label.config(text=prompt_text)
        else:
            # Escribir: mostramos la traducción y pedimos que escriba la palabra en inglés
            prompt_text = f"Escribe la palabra en inglés para:\n\n{self.words[self.current_language][self.current_word]}"
            self.prompt_label.config(text=prompt_text)
        self.entry.delete(0, tk.END)
        self.entry.focus_set()
        self.feedback_label.config(text="")
        # actualizar progreso sencillo
        self.progress_var.set(min(100, self.progress_var.get() + 7))

    def _check_answer(self):
        user_answer = self.entry.get().strip().lower()
        if self.mode == "Traducir":
            correct_answer = self.words[self.current_language][self.current_word].lower()
            is_correct = (user_answer == correct_answer)
        else:
            correct_answer = self.current_word.lower()
            is_correct = (user_answer == correct_answer)

        if is_correct:
            self.score += 1
            self.streak += 1
            self.feedback_label.config(text="¡Correcto! ✅", fg="green")
            self._play_feedback_sound('success')
        else:
            self.feedback_label.config(text=f"Incorrecto. La respuesta es: {correct_answer}", fg="red")
            self._play_feedback_sound('error')
            self.streak = 0
        self._update_score()
        self.streak_label.config(text=f"Racha: {self.streak}")
        # limpiar entrada y avanzar tras un breve delay
        self.root.after(900, lambda: (self.entry.delete(0, tk.END), self._next_word()))

    def _speak_answer(self):
        r = sr.Recognizer()

        def listen_and_fill():
            try:
                with sr.Microphone() as source:
                    self.root.after(0, lambda: self.feedback_label.config(text="Escuchando...", fg="black"))
                    audio = r.listen(source, timeout=5, phrase_time_limit=4)
                user_answer = r.recognize_google(audio, language=self.languages[self.current_language]).lower()
                self.root.after(0, lambda: self.entry.delete(0, tk.END))
                self.root.after(0, lambda: self.entry.insert(0, user_answer))
                self.root.after(0, lambda: self._check_answer())
            except sr.UnknownValueError:
                self.root.after(0, lambda: self.feedback_label.config(text="No se entendió la voz.", fg="orange"))
            except sr.RequestError as e:
                self.root.after(0, lambda: self.feedback_label.config(text=f"Error de reconocimiento: {e}", fg="red"))
            except Exception as e:
                self.root.after(0, lambda: self.feedback_label.config(text=f"Error de micrófono: {e}", fg="red"))

        threading.Thread(target=listen_and_fill, daemon=True).start()

    def _play_audio_file(self, path: str):
        try:
            if _HAS_PLAYSOUND and playsound:
                playsound(path)
            else:
                subprocess.run(["afplay", path])
        except Exception as e:
            print("Audio playback error:", e)

    def _pronounce_word(self):
        # Reproducir la respuesta correcta en el idioma seleccionado
        if self.mode == "Traducir":
            text = self.words[self.current_language][self.current_word]
        else:
            text = self.current_word
        lang_code = self.languages[self.current_language]

        def play_sound():
            filename = None
            try:
                tts = gTTS(text=text, lang=lang_code)
                filename = f"temp_pron_{uuid.uuid4().hex}.mp3"
                tts.save(filename)
                self._play_audio_file(filename)
            except Exception as e:
                self.root.after(0, lambda: self.feedback_label.config(text=f"No se pudo reproducir: {e}", fg="red"))
            finally:
                try:
                    if filename and os.path.exists(filename):
                        os.remove(filename)
                except Exception:
                    pass

        threading.Thread(target=play_sound, daemon=True).start()

    def _update_score(self):
        self.score_label.config(text=f"Puntuación: {self.score}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ProfesorIdiomasApp(root)
    root.mainloop()
