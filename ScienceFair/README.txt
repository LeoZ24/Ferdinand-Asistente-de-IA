            ███╗   ███╗ █████╗ ██████╗ ███████╗    ██████╗ ██╗   ██╗  
            ████╗ ████║██╔══██╗██╔══██╗██╔════╝    ██╔══██╗╚██╗ ██╔╝  
            ██╔████╔██║███████║██║  ██║█████╗      ██████╔╝ ╚████╔╝   
            ██║╚██╔╝██║██╔══██║██║  ██║██╔══╝      ██╔══██╗  ╚██╔╝    
            ██║ ╚═╝ ██║██║  ██║██████╔╝███████╗    ██████╔╝   ██║     
            ╚═╝     ╚═╝╚═╝  ╚═╝╚═════╝ ╚══════╝    ╚═════╝    ╚═╝     
                                                                    
            ██╗     ███████╗ ██████╗                                  
            ██║     ██╔════╝██╔═══██╗                                 
            ██║     █████╗  ██║   ██║                                 
            ██║     ██╔══╝  ██║   ██║                                 
            ███████╗███████╗╚██████╔╝                                 
            ╚══════╝╚══════╝ ╚═════╝                                  
                                                                    
            ███████╗ █████╗ ███╗   ██╗███╗   ██╗ ██████╗ ███╗   ██╗██╗
            ╚══███╔╝██╔══██╗████╗  ██║████╗  ██║██╔═══██╗████╗  ██║██║
            ███╔╝   ███████║██╔██╗ ██║██╔██╗ ██║██║   ██║██╔██╗ ██║██║
            ███╔╝   ██╔══██║██║╚██╗██║██║╚██╗██║██║   ██║██║╚██╗██║██║
            ███████╗██║  ██║██║ ╚████║██║ ╚████║╚██████╔╝██║ ╚████║██║
            ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝
                                                                    
            ███████╗██╗      ██████╗ ██████╗ ███████╗███████╗         
            ██╔════╝██║     ██╔═══██╗██╔══██╗██╔════╝██╔════╝         
            █████╗  ██║     ██║   ██║██████╔╝█████╗  ███████╗         
            ██╔══╝  ██║     ██║   ██║██╔══██╗██╔══╝  ╚════██║         
            ██║     ███████╗╚██████╔╝██║  ██║███████╗███████║         
            ╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝

                Proyecto Feria Cientifica — Juegos y detectores con seguimiento de manos

                Resumen
                --------
                Este repositorio contiene mini-juegos desarrollados con Pygame/Tkinter y sistemas de detección de mano/gestos
                usando OpenCV y MediaPipe. Los juegos están pensados para ejecutarse en pantalla completa y controlarse con la
                cámara (seguimiento de la mano y detección de gestos/posición del dedo índice). También incluye un detector
                de lenguaje de señas basado en heurísticas de landmarks de MediaPipe.

                Estructura principal
                --------------------
                - `main.py`                 - Punto de entrada (si aplica)
                - `Games/`                  - Carpetas y scripts de cada juego
                    - `HandPong.py`          - Pong controlado con la mano (ya incluye mini-UI)
                    - `Dinosaur.py`          - Juego tipo Chrome Dino (se agregó mini-UI)
                    - `FlappyBird.py`        - Versión con Tkinter (se agregó mini-UI)
                    - `RockPaperScissors.py` - Piedra-Papel-Tijera con micro:bit (incluye mini-UI)
                - `Others/`                 - Herramientas y detectores
                    - `SignLenguageDetector.py` - Detector heurístico de letras (se agregó mini-UI)
                - `Assets_*/`               - Imágenes y sonidos usados por los juegos
                - `requirements.txt`       - Dependencias del proyecto
                - `README.txt`             - Este archivo

                Dependencias (recomendadas)
                ---------------------------
                El archivo `requirements.txt` ya incluye las dependencias más importantes. Instalación sugerida:

                1) Crear y activar un entorno virtual (macOS / zsh):

                ```bash
                python3 -m venv venv
                source venv/bin/activate
                ```

                2) Instalar las dependencias:

                ```bash
                pip install -r requirements.txt
                ```

                Contenido actual de `requirements.txt` (resumen):
                - opencv-python
                - mediapipe
                - numpy
                - pygame
                - pillow
                - requests
                - google-generativeai
                - gTTS
                - SpeechRecognition
                - pynput
                - pyserial
                - python-dotenv

                Nota: en macOS puede ser necesario instalar dependencias del sistema para OpenCV/MediaPipe (por ejemplo, via
                brew) si aparecen errores de compilación o instalación.

                API keys y secretos
                -------------------
                Encontré una clave expuesta en el README original. He eliminado esa clave del README para protegerla.
                Por seguridad, nunca almacenes claves en ficheros de texto visibles en el repo.

                Proyecto ScienceFair: Sistema de Control por Gestos

                Descripción
                -----------
                Proyecto que reúne varios mini-juegos y utilidades basadas en visión por computadora y reconocimiento de gestos.
                Los componentes usan OpenCV y MediaPipe para el seguimiento de manos, y Pygame/Tkinter para la interfaz y los juegos.

                Estructura del repositorio
                --------------------------
                - `main.py`			- Módulo principal con control por voz y asistente (integración con Gemini).
                - `Games/`			- Implementaciones de juegos interactivos controlados por gestos.
                    - `HandPong.py`  	- Pong controlado por seguimiento de manos.
                    - `Dinosaur.py`  	- Versión adaptada del juego Chrome Dino.
                    - `FlappyBird.py`	- Implementación con interfaz Tkinter.
                    - `RockPaperScissors.py`	- Piedra-Papel-Tijera con integración opcional a micro:bit.
                - `Others/`			- Utilidades y detectores.
                    - `SignLenguageDetector.py` - Detector heurístico de lenguaje de señas.
                - `Assets_*/` 		- Recursos (imágenes, audio).
                - `requirements.txt` 	- Dependencias del proyecto.
                - `.env` 		- Archivo de configuración para variables de entorno (no incluido en el repositorio).

                Instalación
                -----------
                1. Crear y activar un entorno virtual (macOS / zsh):

                ```bash
                python3 -m venv venv
                source venv/bin/activate
                ```

                2. Instalar dependencias:

                ```bash
                pip install -r requirements.txt
                ```

                Dependencias principales
                ------------------------
                - opencv-python
                - mediapipe
                - numpy
                - pygame
                - pillow
                - requests
                - google-generativeai
                - gTTS
                - SpeechRecognition
                - pynput
                - pyserial
                - python-dotenv

                Configuración de claves y secretos
                ----------------------------------
                Para servicios externos (por ejemplo, la API de Gemini) utilice variables de entorno. Crear un archivo `.env` en la raíz del proyecto y añadir las claves necesarias:

                ```text
                GOOGLE_API_KEY=tu_api_key_aqui
                ```

                Cargar la configuración en Python con `python-dotenv`:

                ```python
                from dotenv import load_dotenv
                import os

                load_dotenv()
                api_key = os.getenv('GOOGLE_API_KEY')
                ```

                Asegúrese de añadir `.env` a `.gitignore` para evitar subir claves al control de versiones.

                Control por voz y asistente (Gemini)
                ----------------------------------
                El módulo `main.py` incluye soporte para comandos de voz. Flujo general:

                - Captura de audio mediante `SpeechRecognition`.
                - Conversión de texto a voz con `gTTS` para respuestas locales.
                - Uso de la API de Gemini (vía paquete `google-generativeai`) para generar respuestas y explicaciones contextuales.

                Requisitos:
                - Configurar `GOOGLE_API_KEY` en `.env`.
                - Asegurarse de que el sistema tenga acceso a la salida de audio (altavoces) y al micrófono.

                Ejecución típica:

                ```bash
                python3 main.py
                ```

                Notas:
                - La latencia de respuesta depende de la conexión a la API de Gemini.
                - Para producción se recomienda gestionar cuotas, reintentos y logs de errores.

                Ejecución de componentes
                ------------------------
                - Juegos:

                ```bash
                python3 Games/HandPong.py
                python3 Games/Dinosaur.py
                python3 Games/FlappyBird.py
                python3 Games/RockPaperScissors.py
                ```

                - Detector de lenguaje de señas:

                ```bash
                python3 Others/SignLenguageDetector.py
                ```

                Resolución de problemas
                -----------------------
                - Verifique que la cámara esté conectada y no esté en uso por otra aplicación.
                - En macOS, compruebe permisos de cámara en Preferencias del Sistema → Seguridad y Privacidad.
                - Si la detección de gestos no es fiable, intente ajustar la posición y la iluminación.

                Buenas prácticas y desarrollo
                ----------------------------
                - Mantenga las claves y secretos fuera del repositorio (usar `.env` o servicios de secretos).
                - Para mejorar la detección de gestos considere añadir calibración inicial o parámetros de sensibilidad por juego.
                - Extraer la UI de instrucciones a un módulo común reduce la duplicación y facilita el mantenimiento.

                Entorno virtual
                ---------------

                ```bash
                source venv/bin/activate
                deactivate
                ```

                Licencia y créditos
                -------------------
                Indique aquí la licencia del proyecto y los créditos a recursos usados (imágenes, sonidos, bibliotecas).