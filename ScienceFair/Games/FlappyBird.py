from PIL import Image, ImageTk
import tkinter as tk 
from pygame import mixer 
import random
import cv2
import mediapipe as mp
import os
import threading
import time

# Obtener la ruta base del directorio actual
base_path = os.path.dirname(os.path.abspath(__file__))

mixer.init() 
window = tk.Tk()
window.attributes("-fullscreen", True)
window.title('Flappy Bird')

# Variables de juego
x = 150
y = 300
score = 0
speed = 15
game_over = False
paused = False  # Nuevo: indica si el juego está en pausa
last_hand_time = time.time()  # Nuevo: tiempo de la última detección de mano

# Cargar imágenes
img_bird = Image.open(os.path.join(base_path, "Assets_Flappy", 'Images', 'bird.png'))
img_bird = ImageTk.PhotoImage(img_bird)

img_pipe_down = Image.open(os.path.join(base_path, "Assets_Flappy", 'Images', 'pipe.png'))  # 104x900
img_pipe_top = img_pipe_down.rotate(180)
img_pipe_down = ImageTk.PhotoImage(img_pipe_down)
img_pipe_top = ImageTk.PhotoImage(img_pipe_top)

img_reset = Image.open(os.path.join(base_path, "Assets_Flappy", 'Images', 'reiniciar.png'))
img_reset = ImageTk.PhotoImage(img_reset)

# Crear canvas que ocupe toda la ventana
canvas = tk.Canvas(window, highlightthickness=0, bg='#649dfa')
canvas.place(relwidth=1, relheight=1)

text_score = canvas.create_text(50, 50, text='0', fill='white', font=('D3 Egoistism outline', 30))
bird = canvas.create_image(x, y, anchor='nw', image=img_bird)

# Crear lista de tuberías
pipes = []
pipe_gap_x = 500  # Separación horizontal entre cada par

def create_pipe(x_position):
    h = window.winfo_height()
    center_gap = h // 2  # Center the gap around the middle of the screen
    offset = random.randint(-100, 100)  # Add a small random offset for variation
    num = center_gap + offset
    pipe_down = canvas.create_image(x_position, num + 160, anchor='nw', image=img_pipe_down)
    pipe_top = canvas.create_image(x_position, num - 900, anchor='nw', image=img_pipe_top)
    return {'top': pipe_top, 'down': pipe_down}

for i in range(3):
    pipes.append(create_pipe(1200 + i * pipe_gap_x))

mixer.music.load(os.path.join(base_path, "Assets_Flappy", 'Audio', 'FlappyBird_audio_swoosh.wav'))
mixer.music.play(loops=0)

# Configuración de MediaPipe para hand tracking
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)

# VideoCapture
cap = cv2.VideoCapture(0)

# Variables compartidas (protegidas por lock si es necesario)
hand_y_global = None
camera_image = None  # Será una ImageTk.PhotoImage para mostrar en lbl_camera

# Thread de procesamiento de vídeo
def video_processing():
    global hand_y_global, camera_image
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        # Aumentar la resolución para mejor detección (por ejemplo, redimensionar a 640x480)
        frame = cv2.resize(frame, (640, 480))
        frame = cv2.flip(frame, 1)  # Modo espejo
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)
        # Si se detectan manos, extraer la coordenada Y del dedo índice (landmark 8)
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            hand_y_global = hand_landmarks.landmark[8].y  # Valor normalizado
            # Dibujar landmarks sobre la imagen para la vista de cámara
            mp_drawing.draw_landmarks(frame_rgb, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        else:
            hand_y_global = None

        # Redimensionar para el display en la etiqueta (400x300)
        pil_image = Image.fromarray(frame_rgb)
        pil_image = pil_image.resize((400, 300))
        # Actualizar la variable compartida para la imagen
        camera_image = ImageTk.PhotoImage(image=pil_image)
        
        # Reducir la frecuencia de procesamiento (p. ej., 20 FPS)
        time.sleep(0.05)

# Iniciar el thread de vídeo
video_thread = threading.Thread(target=video_processing, daemon=True)
video_thread.start()

# Función que actualiza la posición del pájaro basado en la mano
def update_hand_and_camera():
    global y, hand_y_global, camera_image, paused, last_hand_time
    # Actualiza la posición del pájaro si se detecta la mano
    if hand_y_global is not None:
        new_y = int(hand_y_global * (window.winfo_height() - 100))
        y = new_y
        canvas.coords(bird, x, y)
        # Si estaba en pausa, reanudar
        if paused:
            paused = False
            lbl_pause.place_forget()
        last_hand_time = time.time()
    else:
        # Si no hay mano y han pasado más de 0.5s, pausar
        if not paused and (time.time() - last_hand_time) > 0.3 and not game_over:
            paused = True
            lbl_pause.place(relx=0.5, rely=0.4, anchor='center')
    # Actualiza la imagen de la cámara
    if camera_image is not None:
        lbl_camera.config(image=camera_image)
        lbl_camera.image = camera_image  # mantener referencia
    window.after(50, update_hand_and_camera)

def move_bird():
    global x, y
    if not paused:
        y += 5
        canvas.coords(bird, x, y)
        if y < 0 or y > window.winfo_height():
            game_end()
    if not game_over:
        window.after(50, move_bird)

def move_pipe():
    global score, game_over, speed
    if not paused:
        for pipe in pipes:
            canvas.move(pipe['top'], -speed, 0)
            canvas.move(pipe['down'], -speed, 0)
            if canvas.coords(pipe['down'])[0] < -100:
                score += 1
                speed += 1
                mixer.music.load(os.path.join(base_path, "Assets_Flappy", 'Audio', 'FlappyBird_audio_point.wav'))
                mixer.music.play(loops=0)
                canvas.itemconfigure(text_score, text=str(score))
                h = window.winfo_height()
                num = random.choice(range(160, h, 160))
                canvas.coords(pipe['down'], window.winfo_width(), num + 160)
                canvas.coords(pipe['top'], window.winfo_width(), num - 900)
            # Comprobación de colisiones
            bird_bbox = canvas.bbox(bird)
            pipe_down_bbox = canvas.bbox(pipe['down'])
            pipe_top_bbox = canvas.bbox(pipe['top'])
            if bird_bbox and pipe_down_bbox and pipe_top_bbox:
                # Reduce hitbox size for bird
                bird_bbox = (
                    bird_bbox[0] + 7.5,  # Shrink left
                    bird_bbox[1] + 7.5,  # Shrink top
                    bird_bbox[2] - 7.5,  # Shrink right
                    bird_bbox[3] - 7.5   # Shrink bottom
                )
                # Reduce hitbox size for pipes
                pipe_down_bbox = (
                    pipe_down_bbox[0] + 7.5,
                    pipe_down_bbox[1] + 7.5,
                    pipe_down_bbox[2] - 7.5,
                    pipe_down_bbox[3] - 7.5
                )
                pipe_top_bbox = (
                    pipe_top_bbox[0] + 7.5,
                    pipe_top_bbox[1] + 7.5,
                    pipe_top_bbox[2] - 7.5,
                    pipe_top_bbox[3] - 7.5
                )
                if bird_bbox[0] < pipe_down_bbox[2] and bird_bbox[2] > pipe_down_bbox[0]:
                    if bird_bbox[1] < pipe_top_bbox[3] or bird_bbox[3] > pipe_down_bbox[1]:
                        game_end()
    if not game_over:
        window.after(50, move_pipe)

def reset_game():
    global x, y, score, speed, game_over
    x = 150
    y = 300
    score = 0
    speed = 15
    game_over = False
    canvas.coords(bird, x, y)
    canvas.itemconfigure(text_score, text="0")
    for i, pipe in enumerate(pipes):
        new_x = 1200 + i * pipe_gap_x
        h = window.winfo_height()
        num = random.choice(range(160, h, 160))
        canvas.coords(pipe['down'], new_x, num + 160)
        canvas.coords(pipe['top'], new_x, num - 900)
    lbl_game_over.place_forget()
    bt_reset.place_forget()
    move_bird()
    move_pipe()
    mixer.music.load(os.path.join(base_path, "Assets_Flappy", 'Audio', 'FlappyBird_audio_swoosh.wav'))
    mixer.music.play(loops=0)

def game_end():
    global game_over
    game_over = True
    lbl_game_over.place(relx=0.5, rely=0.5, anchor='center')
    bt_reset.place(relx=0.5, rely=0.7, anchor='center')
    mixer.music.load(os.path.join(base_path, "Assets_Flappy", 'Audio', 'FlappyBird_audio_hit.wav'))
    mixer.music.play(loops=0)
    while mixer.music.get_busy():
        window.update()
    mixer.music.load(os.path.join(base_path, "Assets_Flappy", 'Audio', 'FlappyBird_audio_die.wav'))
    mixer.music.play(loops=0)
    window.after(2000, reset_game)

# Widgets para game over y reinicio
lbl_game_over = tk.Label(window, text='Game Over !', font=('D3 Egoistism outline', 30), fg='white', bg='#649dfa')
lbl_pause = tk.Label(window, text='Detectando mano...', font=('D3 Egoistism outline', 60), fg='white', bg='#649dfa')  # Nuevo widget para pausa
bt_reset = tk.Button(window, border=0, image=img_reset, activebackground='#649dfa', bg='#649dfa', command=reset_game)

window.call('wm', 'iconphoto', window._w, img_bird) 

# Mostrar video de la cámara en la esquina superior derecha
lbl_camera = tk.Label(window, bd=2, relief="solid")
lbl_camera.place(relx=1, x=-10, y=10, anchor='ne')

# Iniciar actualizaciones: se separa el procesamiento de vídeo (en el thread)
window.after(50, update_hand_and_camera)
window.after(250, move_bird)
window.after(500, move_pipe)

window.mainloop()
cap.release()
hands.close()