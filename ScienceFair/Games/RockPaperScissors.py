import cv2
import mediapipe as mp
import math
import serial
import time
import sys
import pygame
import numpy as np
from collections import Counter

try:
    # --- IMPORTANTE: '/dev/tty.usbmodem11402' cambiar por el puerto en caso de que se cambie ---
    microbit_port = '/dev/tty.usbmodem11402'
    microbit = serial.Serial(microbit_port, 115200, timeout=1)
    print(f"Conexión con micro:bit en {microbit_port} exitosa.")
    time.sleep(2) # 2 segundos para que la conexión se establezca firmemente
except serial.SerialException:
    print(f"Error: No se pudo conectar con la micro:bit en el puerto {microbit_port}.")
    print("El programa continuará sin enviar comandos al robot.")
    microbit = None


# Guardará el último gesto enviado para no repetir comandos
last_sent_gesture = None
# Tiempo en segundos para esperar entre rondas y no inundar a la micro:bit
COMMAND_COOLDOWN = 0.1
last_command_time = 0

# Detección de manos
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# Función para calcular distancia entre puntos
def calculate_distance(point1, point2):
    return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)

# Función para detectar dedos arriba
def count_fingers(hand_landmarks):
    tips_ids = [4, 8, 12, 16, 20]
    fingers = []
    
    # Pulgar (depende de la orientación de la mano, puede necesitar ajuste)
    # Compara la punta del pulgar con el nudillo para ver si está extendido
    if hand_landmarks.landmark[tips_ids[0]].x < hand_landmarks.landmark[tips_ids[0] - 1].x:
        fingers.append(1)
    else:
        fingers.append(0)
    
    # Otros 4 dedos
    for id in range(1, 5):
        if hand_landmarks.landmark[tips_ids[id]].y < hand_landmarks.landmark[tips_ids[id] - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)
    
    return fingers

# Función para detectar gestos
def detect_gesture(fingers, hand_landmarks):
    if sum(fingers) <= 0.5:
        return "Piedra"
    if sum(fingers) >= 4.5:
        return "Papel"
    if fingers[1] == 1 and fingers[2] == 1 and sum(fingers) == 2:
        index_tip = hand_landmarks.landmark[8]
        middle_tip = hand_landmarks.landmark[12]
        distance = calculate_distance(index_tip, middle_tip)
        if distance > 0.05:
            return "Tijera"
    return None # Devolvemos None si no hay un gesto claro

# ### MODIFICADO ### - Función para enviar el comando al robot y devolver su jugada
def enviar_comando_a_robot(movimiento_humano):
    global microbit
    
    # Lógica para que el robot gane
    decision_robot = ""
    # se pasa a minúsculas para que coincida con el código de MakeCode
    if movimiento_humano.lower() == "piedra":
        decision_robot = "papel"
    elif movimiento_humano.lower() == "papel":
        decision_robot = "tijera"
    elif movimiento_humano.lower() == "tijera":
        decision_robot = "piedra"
    
    if decision_robot and microbit: # Si hay conexión y una decisión válida
        print(f"Humano jugó: {movimiento_humano}. Enviando comando al robot para que juegue: '{decision_robot}'")
        # se envia el comando como bytes y con un salto de línea '\n' al final.
        microbit.write(f"{decision_robot}\n".encode('utf-8'))
        
    return decision_robot # Devolvemos la jugada del robot para mostrarla

def enviar_reinicio_microbit():
    global microbit
    if microbit:
        try:
            microbit.write(b'reinicio\n')
            print("Señal de reinicio enviada a la micro:bit.")
        except Exception as e:
            print(f"Error enviando señal de reinicio: {e}")

# --- Configuración y bucle principal ---
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)

# --- Inicializar Pygame para la interfaz moderna ---
pygame.init()
try:
    pygame.mixer.quit()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
except Exception as e:
    print(f"Error inicializando pygame.mixer: {e}")

# Cargar sonidos (asegúrate de que las rutas son correctas)
try:
    START_SOUND = pygame.mixer.Sound('Games/Assets_RockPaperScissors/StartingSound.mp3')
    END_SOUND = pygame.mixer.Sound('Games/Assets_RockPaperScissors/EndSound.mp3')
    START_SOUND.set_volume(0.7)
    END_SOUND.set_volume(0.8)
    print("Sonidos cargados correctamente.")
except Exception as e:
    print(f"No se pudieron cargar los sonidos, revisa la ruta: {e}")
    START_SOUND = END_SOUND = None

# Configurar pantalla completa
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h

# Colores para la interfaz
NEON_BLUE = (0, 195, 255)
NEON_GREEN = (57, 255, 20)
WHITE = (255, 255, 255)
BACKGROUND = (10, 10, 30)

def detect_thumbs_up(hand_landmarks):
    if not hand_landmarks:
        return False
    thumb_tip = hand_landmarks.landmark[4]
    thumb_mcp = hand_landmarks.landmark[2]
    index_pip = hand_landmarks.landmark[6]
    pinky_pip = hand_landmarks.landmark[18]
    is_up = thumb_tip.y < thumb_mcp.y and thumb_tip.y < index_pip.y and thumb_tip.y < pinky_pip.y
    return is_up

def draw_rounded_rect(surface, color, rect, radius):
    pygame.draw.rect(surface, color, rect, border_radius=radius)

def show_instructions():
    clock = pygame.time.Clock()
    instructions = [
        ("¡Bienvenido a Piedra, Papel o Tijera!", 40, (255, 255, 255)),
        ("Juega contra el robot usando gestos con la mano", 28, (200, 200, 200)),
        ("", 20, (255, 255, 255)),
        ("Cómo jugar:", 32, (255, 255, 255)),
        ("• Puño cerrado = Piedra", 24, (200, 200, 200)),
        ("• Mano abierta = Papel", 24, (200, 200, 200)),
        ("• Dedos índice y medio = Tijera", 24, (200, 200, 200)),
        ("", 20, (255, 255, 255)),
        ("Haz un pulgar arriba para comenzar", 32, (98, 212, 155))
    ]
    waiting_for_thumbs_up = True
    while waiting_for_thumbs_up:
        ret, frame = cap.read()
        if not ret: continue
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)
        frame_with_landmarks = frame.copy()
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame_with_landmarks, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        frame_rgb = cv2.resize(frame_with_landmarks, (SCREEN_WIDTH, SCREEN_HEIGHT))
        frame_surface = pygame.surfarray.make_surface(np.rot90(cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2RGB)))
        frame_surface = pygame.transform.flip(frame_surface, True, False)
        screen.blit(frame_surface, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        popup_height, popup_width = 400, 800
        popup_x, popup_y = (SCREEN_WIDTH - popup_width) // 2, SCREEN_HEIGHT - popup_height - 50
        popup_surface = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
        draw_rounded_rect(popup_surface, (30, 30, 40, 230), pygame.Rect(0, 0, popup_width, popup_height), 20)
        y_offset = 30
        for text, size, color in instructions:
            font = pygame.font.Font(None, size)
            text_surface = font.render(text, True, color)
            text_rect = text_surface.get_rect(center=(popup_width//2, y_offset))
            popup_surface.blit(text_surface, text_rect)
            y_offset += size + 10
        screen.blit(popup_surface, (popup_x, popup_y))
        if results.multi_hand_landmarks and detect_thumbs_up(results.multi_hand_landmarks[0]):
            pygame.time.wait(500)
            waiting_for_thumbs_up = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit(), cv2.destroyAllWindows(), microbit.close() if microbit else None, sys.exit()
        pygame.display.flip()
        clock.tick(60)

def draw_centered_text(surface, text, size, color, y_offset=0, shadow=True):
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + y_offset))
    if shadow:
        shadow_surface = font.render(text, True, (0,0,0, 100))
        shadow_rect = shadow_surface.get_rect(center=(SCREEN_WIDTH//2+3, SCREEN_HEIGHT//2 + y_offset+3))
        surface.blit(shadow_surface, shadow_rect)
    surface.blit(text_surface, rect)

def draw_hand_landmarks_on_surface(surface, frame, results):
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            h, w = frame.shape[:2]
            for connection in mp_hands.HAND_CONNECTIONS:
                start = hand_landmarks.landmark[connection[0]]
                end = hand_landmarks.landmark[connection[1]]
                x0, y0 = int(start.x * SCREEN_WIDTH), int(start.y * SCREEN_HEIGHT)
                x1, y1 = int(end.x * SCREEN_WIDTH), int(end.y * SCREEN_HEIGHT)
                pygame.draw.line(surface, NEON_BLUE, (x0, y0), (x1, y1), 4)
            for lm in hand_landmarks.landmark:
                x, y = int(lm.x * SCREEN_WIDTH), int(lm.y * SCREEN_HEIGHT)
                pygame.draw.circle(surface, NEON_GREEN, (x, y), 8)

def game_loop():
    global last_command_time
    
    # ### NUEVO: Inicialización de puntuaciones ###
    user_score = 0
    robot_score = 0
    
    clock = pygame.time.Clock()
    running = True
    while running:
        enviar_reinicio_microbit()
        countdown = ["Piedra...", "Papel...", "o...", "Tijera...", "¡YA!"]
        countdown_times = [0.8, 0.8, 0.4, 0.8, 1.0] # Tiempos para cada palabra
        gesture_candidates = []

        # --- Bucle de cuenta atrás ---
        for i, word in enumerate(countdown):
            word_start = time.time()
            if i < len(countdown) - 1 and START_SOUND: START_SOUND.play()
            if i == len(countdown) - 1 and END_SOUND: END_SOUND.play()

            while time.time() - word_start < countdown_times[i]:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        pygame.quit(), cv2.destroyAllWindows(), microbit.close() if microbit else None, sys.exit()

                ret, frame = cap.read()
                if not ret: continue
                frame = cv2.flip(frame, 1)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(frame_rgb)
                
                frame_show = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
                frame_show = cv2.cvtColor(frame_show, cv2.COLOR_BGR2RGB)
                frame_surface = pygame.surfarray.make_surface(np.rot90(frame_show))
                frame_surface = pygame.transform.flip(frame_surface, True, False)
                screen.blit(frame_surface, (0, 0))
                
                draw_hand_landmarks_on_surface(screen, frame_show, results)
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((20, 20, 40, 180))
                screen.blit(overlay, (0, 0))
                
                draw_centered_text(screen, word, 90, NEON_BLUE, y_offset=0)
                pygame.display.flip()
                clock.tick(60)

                # Durante la última palabra ("¡YA!"), se capturan los gestos
                if i == len(countdown) - 1 and results.multi_hand_landmarks:
                    hand_landmarks = results.multi_hand_landmarks[0]
                    fingers = count_fingers(hand_landmarks)
                    gesture = detect_gesture(fingers, hand_landmarks)
                    if gesture:
                        gesture_candidates.append(gesture)

        # --- Procesamiento del resultado de la ronda ---
        gesture_detected = None
        if gesture_candidates:
            gesture_detected = Counter(gesture_candidates).most_common(1)[0][0]

        # ### MODIFICADO: Lógica de resultado y puntuación ###
        robot_move = ""
        user_play_text = ""
        robot_play_text = ""
        
        if gesture_detected:
            robot_move = enviar_comando_a_robot(gesture_detected)
            if robot_move: # Si el robot respondió, significa que ganó
                robot_score += 1
            user_play_text = f"Tú jugaste: {gesture_detected}"
            robot_play_text = f"Robot jugó: {robot_move}"
        else:
            user_play_text = "No se detectó tu gesto."
            robot_play_text = "El robot espera..."

        # --- Bucle para mostrar el resultado y la puntuación ---
        result_start = time.time()
        while time.time() - result_start < 4.0: # Aumentado a 4 segundos para leer
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                     pygame.quit(), cv2.destroyAllWindows(), microbit.close() if microbit else None, sys.exit()
            
            ret, frame = cap.read()
            if not ret: continue
            frame = cv2.flip(frame, 1)
            frame_show = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
            frame_show = cv2.cvtColor(frame_show, cv2.COLOR_BGR2RGB)
            frame_surface = pygame.surfarray.make_surface(np.rot90(frame_show))
            frame_surface = pygame.transform.flip(frame_surface, True, False)
            screen.blit(frame_surface, (0, 0))
            
            draw_hand_landmarks_on_surface(screen, frame_show, hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((20, 20, 40, 180))
            screen.blit(overlay, (0, 0))
            
            popup_width, popup_height = 800, 280  # Pop-up más alto
            popup_x, popup_y = (SCREEN_WIDTH - popup_width) // 2, (SCREEN_HEIGHT - popup_height) // 2
            
            shadow = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
            draw_rounded_rect(shadow, (0,0,0,80), pygame.Rect(0,0,popup_width,popup_height), 32)
            screen.blit(shadow, (popup_x+6, popup_y+6))
            
            popup_surface = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
            draw_rounded_rect(popup_surface, (30, 30, 60, 220), pygame.Rect(0,0,popup_width,popup_height), 32)
            screen.blit(popup_surface, (popup_x, popup_y))

            # Mostrar jugadas y puntuación
            draw_centered_text(screen, user_play_text, 65, NEON_GREEN, y_offset=-60)
            draw_centered_text(screen, robot_play_text, 65, NEON_BLUE, y_offset=15)
            score_text = f"Puntuación: Tú {user_score} - Robot {robot_score}"
            draw_centered_text(screen, score_text, 55, WHITE, y_offset=90)

            pygame.display.flip()
            clock.tick(60)

        # --- Preguntar si quiere jugar de nuevo ---
        waiting_for_restart = True
        while waiting_for_restart:
            ret, frame = cap.read()
            if not ret: continue
            frame = cv2.flip(frame, 1)
            results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
            frame_show = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
            frame_show = cv2.cvtColor(frame_show, cv2.COLOR_BGR2RGB)
            frame_surface = pygame.surfarray.make_surface(np.rot90(frame_show))
            frame_surface = pygame.transform.flip(frame_surface, True, False)
            screen.blit(frame_surface, (0, 0))
            
            draw_hand_landmarks_on_surface(screen, frame_show, results)
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((20, 20, 40, 180))
            screen.blit(overlay, (0, 0))
            
            draw_centered_text(screen, "¿Jugar de nuevo? Pulgar arriba para reiniciar", 60, WHITE, y_offset=0)
            
            if results.multi_hand_landmarks and detect_thumbs_up(results.multi_hand_landmarks[0]):
                pygame.time.wait(400)
                waiting_for_restart = False
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    waiting_for_restart = False
                    running = False # Termina el bucle principal del juego
            
            pygame.display.flip()
            clock.tick(60)

# --- INICIO DEL PROGRAMA ---
show_instructions()
game_loop()

# Liberar recursos al salir
print("Saliendo del juego...")
hands.close()
cap.release()
cv2.destroyAllWindows()
pygame.quit()
if microbit:
    microbit.close()
    print("Conexión con micro:bit cerrada.")
sys.exit()
