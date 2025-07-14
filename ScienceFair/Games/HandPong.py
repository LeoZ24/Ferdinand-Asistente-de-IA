import cv2
import mediapipe as mp
import pygame
import sys
import random
import time
import numpy as np
from math import sin

# -----------------------------
# CONFIGURACIÓN DE PYGAME Y DEL JUEGO
# -----------------------------
pygame.init()
pygame.mixer.init()  # Inicializar el sistema de sonido

# Cargar efectos de sonido
try:
    PADDLE_HIT = pygame.mixer.Sound('Games/Assets_HandPong/PadleHit.mp3')
    SCORE_SOUND = pygame.mixer.Sound('Games/Assets_HandPong/Score.mp3')
    WALL_HIT = pygame.mixer.Sound('Games/Assets_HandPong/WallHit.mp3')
    
    # Ajustar volumen
    PADDLE_HIT.set_volume(0.6)
    SCORE_SOUND.set_volume(0.7)
    WALL_HIT.set_volume(0.5)
except:
    print("No se pudieron cargar algunos efectos de sonido")
    PADDLE_HIT = SCORE_SOUND = WALL_HIT = None

# Configurar pantalla completa real
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
info = pygame.display.Info()
total_width = info.current_w
total_height = info.current_h

# Área de la cámara (1/4 del ancho)
cam_width = total_width // 4
cam_height = total_height

# Área del juego de Pong (3/4 del ancho)
pong_width = total_width - cam_width
pong_height = total_height

pygame.display.set_caption("Pong con Hand Tracking y Cámara")
clock = pygame.time.Clock()

# Dimensiones y objetos del juego ajustados a la nueva resolución
paddle_width = int(pong_width * 0.012)
paddle_height = int(pong_height * 0.18)
player_paddle = pygame.Rect(40, pong_height // 2 - paddle_height // 2, paddle_width, paddle_height)
ai_paddle = pygame.Rect(pong_width - 60, pong_height // 2 - paddle_height // 2, paddle_width, paddle_height)
ball = pygame.Rect(pong_width // 2 - 12, pong_height // 2 - 12, 24, 24)

# Velocidades de la pelota
ball_speed_x = pong_width * 0.015
ball_speed_y = pong_height * 0.012

# Ajustar colores para mejor visibilidad en pantalla completa
NEON_BLUE = (0, 195, 255)
NEON_PINK = (255, 0, 153)
NEON_GREEN = (57, 255, 20)
NEON_PURPLE = (200, 0, 255)
NEON_YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BACKGROUND_COLOR = (10, 10, 30)
GRID_COLOR = (30, 30, 60)

class ParticleEffect:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.particles = []
        self.color = color
        
    def add_particles(self, speed_x=0):
        for _ in range(10):
            particle = {
                'x': self.x,
                'y': self.y,
                'velocity_x': random.uniform(-2 + speed_x, 2 + speed_x),
                'velocity_y': random.uniform(-2, 2),
                'lifetime': 255,
                'size': random.randint(2, 4)
            }
            self.particles.append(particle)
    
    def update_and_draw(self, surface):
        remaining_particles = []
        for particle in self.particles:
            particle['x'] += particle['velocity_x']
            particle['y'] += particle['velocity_y']
            particle['lifetime'] -= 15
            
            if particle['lifetime'] > 0:
                alpha = min(255, particle['lifetime'])
                color_with_alpha = (*self.color, alpha)
                particle_surface = pygame.Surface((particle['size'], particle['size']), pygame.SRCALPHA)
                pygame.draw.circle(particle_surface, color_with_alpha, 
                                 (particle['size']//2, particle['size']//2), 
                                 particle['size']//2)
                surface.blit(particle_surface, (int(particle['x']), int(particle['y'])))
                remaining_particles.append(particle)
        
        self.particles = remaining_particles

class Trail:
    def __init__(self, color):
        self.positions = []
        self.color = color
        self.max_length = 10
    
    def add_position(self, x, y):
        self.positions.append((x, y))
        if len(self.positions) > self.max_length:
            self.positions.pop(0)
    
    def draw(self, surface):
        for i, pos in enumerate(self.positions):
            alpha = int((i / len(self.positions)) * 255)
            color_with_alpha = (*self.color, alpha)
            size = int((i / len(self.positions)) * 14)
            particle_surface = pygame.Surface((14, 14), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, color_with_alpha, (7, 7), size//2)
            surface.blit(particle_surface, (int(pos[0] - 7), int(pos[1] - 7)))

class ScoreEffect:
    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y
        self.initial_y = y
        self.text = text
        self.color = color
        self.alpha = 255
        self.time = 0
    
    def update_and_draw(self, surface):
        self.time += 0.1
        self.y = self.initial_y - 50 * sin(self.time)
        self.alpha -= 5
        
        if self.alpha > 0:
            font = pygame.font.Font(None, 40)
            text_surface = font.render(self.text, True, self.color)
            text_surface.set_alpha(self.alpha)
            surface.blit(text_surface, (self.x, self.y))
            return True
        return False

class BallTrail:
    def __init__(self, color):
        self.positions = []
        self.color = color
        self.max_length = 15
    
    def add_position(self, x, y):
        self.positions.append((x, y))
        if len(self.positions) > self.max_length:
            self.positions.pop(0)
    
    def draw(self, surface, offset_x=0):
        for i, pos in enumerate(self.positions):
            alpha = int((i / len(self.positions)) * 200)
            size = int((i / len(self.positions)) * 14)
            particle_surface = pygame.Surface((14, 14), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, (*self.color, alpha), (7, 7), size//2)
            surface.blit(particle_surface, (int(pos[0] + offset_x - 7), int(pos[1] - 7)))

class CollisionEffect:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.particles = []
        self.color = color
        self.lifetime = 30
        self.create_particles()
    
    def create_particles(self):
        for _ in range(20):
            angle = random.uniform(0, 2 * np.pi)
            speed = random.uniform(2, 8)
            self.particles.append({
                'x': self.x,
                'y': self.y,
                'vx': speed * np.cos(angle),
                'vy': speed * np.sin(angle),
                'size': random.randint(2, 6),
                'alpha': 255
            })
    
    def update_and_draw(self, surface, offset_x=0):
        if self.lifetime <= 0:
            return False
        
        self.lifetime -= 1
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['alpha'] = int(p['alpha'] * 0.9)
            
            if p['alpha'] > 0:
                particle_surface = pygame.Surface((p['size'], p['size']), pygame.SRCALPHA)
                pygame.draw.circle(particle_surface, (*self.color, p['alpha']), 
                                 (p['size']//2, p['size']//2), p['size']//2)
                surface.blit(particle_surface, (int(p['x'] + offset_x), int(p['y'])))
        
        return True

class ScoreFlash:
    def __init__(self, x, y, score, color):
        self.x = x
        self.y = y
        self.score = score
        self.color = color
        self.alpha = 255
        self.scale = 2.0
        self.lifetime = 60
    
    def update_and_draw(self, surface, offset_x=0):
        if self.lifetime <= 0:
            return False
            
        self.lifetime -= 1
        self.scale = max(1.0, self.scale * 0.95)
        self.alpha = int(self.alpha * 0.95)
        
        font = pygame.font.Font(None, int(70 * self.scale))
        text = font.render(str(self.score), True, self.color)
        text.set_alpha(self.alpha)
        
        text_rect = text.get_rect(center=(self.x + offset_x, self.y))
        surface.blit(text, text_rect)
        
        return True

# Dimensiones totales de la ventana
total_width, total_height = 1440, 700
# Área de la cámara (1/2 del ancho)
cam_width = total_width // 2   
cam_height = total_height          
# Área del juego de Pong (1/2 del ancho)
pong_width = total_width - cam_width  
pong_height = total_height             

# Crear la ventana principal
screen = pygame.display.set_mode((total_width, total_height))
pygame.display.set_caption("Pong con Hand Tracking y Cámara")
clock = pygame.time.Clock()

# -----------------------------
# CONFIGURACIÓN DE MEDIAPIPE PARA HAND TRACKING
# -----------------------------
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
hands = mp_hands.Hands(static_image_mode=False,
                       max_num_hands=1,
                       min_detection_confidence=0.7,
                       min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)

def detect_thumbs_up(hand_landmarks):
    """
    Detecta si la mano está haciendo un gesto de pulgar arriba
    """
    if not hand_landmarks:
        return False
    
    # Puntos clave del pulgar
    thumb_tip = hand_landmarks.landmark[4]
    thumb_mcp = hand_landmarks.landmark[2]
    
    # Puntos clave de otros dedos
    index_tip = hand_landmarks.landmark[8]
    middle_tip = hand_landmarks.landmark[12]
    ring_tip = hand_landmarks.landmark[16]
    pinky_tip = hand_landmarks.landmark[20]
    
    # Verificar si el pulgar está arriba y los otros dedos están cerrados
    thumbs_up = (thumb_tip.y < thumb_mcp.y and  # Pulgar arriba
                all(finger.y > thumb_mcp.y for finger in [index_tip, middle_tip, ring_tip, pinky_tip]))  # Otros dedos cerrados
    
    return thumbs_up

def draw_rounded_rect(surface, color, rect, radius):
    """
    Dibuja un rectángulo con esquinas redondeadas
    """
    pygame.draw.rect(surface, color, rect, border_radius=radius)

def show_instructions():
    """
    Muestra un pop-up moderno de instrucciones y espera el gesto de pulgar arriba
    """
    instructions = [
        ("¡Bienvenido a Hand Pong!", 40, (255, 255, 255)),
        ("Controla el juego con tu mano", 28, (200, 200, 200)),
        ("", 20, (255, 255, 255)),
        (" Cómo jugar:", 32, (255, 255, 255)),
        ("• Mueve tu mano arriba y abajo para controlar la paleta", 24, (200, 200, 200)),
        ("• Tu dedo índice es el punto de control", 24, (200, 200, 200)),
        ("• Evita que la pelota pase tu paleta", 24, (200, 200, 200)),
        ("", 20, (255, 255, 255)),
        (" Haz un pulgar arriba para comenzar", 32, (98, 212, 155))
    ]
    
    waiting_for_thumbs_up = True
    popup_alpha = 0  # Para la animación de entrada
    
    while waiting_for_thumbs_up:
        ret, frame = cap.read()
        if not ret:
            continue
            
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)
        
        # Convertir frame para Pygame
        frame_rgb = cv2.resize(frame_rgb, (total_width, total_height))
        cam_surface = pygame.surfarray.make_surface(frame_rgb)
        cam_surface = pygame.transform.rotate(cam_surface, -90)
        cam_surface = pygame.transform.flip(cam_surface, True, False)
        
        # Mostrar pantalla completa de la cámara
        screen.blit(cam_surface, (0, 0))
        
        # Crear superficie semi-transparente para el fondo oscuro
        overlay = pygame.Surface((total_width, total_height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        screen.blit(overlay, (0, 0))
        
        # Animación de entrada del pop-up
        if popup_alpha < 255:
            popup_alpha += 10
        
        # Crear el pop-up de instrucciones
        popup_height = 400
        popup_width = 800
        popup_x = (total_width - popup_width) // 2
        popup_y = total_height - popup_height - 50  # 50px desde el fondo
        
        # Dibujar el pop-up con fondo semi-transparente y bordes redondeados
        popup_surface = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
        draw_rounded_rect(popup_surface, (30, 30, 40, min(230, popup_alpha)), 
                         pygame.Rect(0, 0, popup_width, popup_height), 20)
        
        # Mostrar instrucciones en el pop-up
        y_offset = 30
        for text, size, color in instructions:
            font = pygame.font.Font(None, size)
            text_surface = font.render(text, True, (*color, min(255, popup_alpha)))
            text_rect = text_surface.get_rect(center=(popup_width//2, y_offset))
            popup_surface.blit(text_surface, text_rect)
            y_offset += size + 10
        
        screen.blit(popup_surface, (popup_x, popup_y))
        
        # Detectar pulgar arriba y mostrar feedback visual
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            if detect_thumbs_up(hand_landmarks):
                # Mostrar círculo verde de confirmación
                confirmation_surface = pygame.Surface((100, 100), pygame.SRCALPHA)
                pygame.draw.circle(confirmation_surface, (98, 212, 155, min(255, popup_alpha)), (50, 50), 40)
                pygame.draw.circle(confirmation_surface, (255, 255, 255, min(255, popup_alpha)), (50, 50), 40, 3)
                check_font = pygame.font.Font(None, 50)
                check_text = check_font.render("✓", True, (255, 255, 255, min(255, popup_alpha)))
                check_rect = check_text.get_rect(center=(50, 50))
                confirmation_surface.blit(check_text, check_rect)
                screen.blit(confirmation_surface, (total_width//2 - 50, total_height//2 - 50))
                
                # Esperar un momento antes de comenzar
                pygame.display.flip()
                pygame.time.wait(500)
                waiting_for_thumbs_up = False
                continue
        
        # Manejar eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        pygame.display.flip()
        clock.tick(60)
    
    # Transición suave para salir de las instrucciones
    for alpha in range(255, -1, -15):
        screen.fill((0, 0, 0))
        overlay.set_alpha(alpha)
        screen.blit(overlay, (0, 0))
        pygame.display.flip()
        clock.tick(60)

# Dimensiones y objetos del juego (coordenadas relativas al área de Pong)
paddle_width, paddle_height = 10, 80
player_paddle = pygame.Rect(10, pong_height // 2 - paddle_height // 2, paddle_width, paddle_height)
ai_paddle = pygame.Rect(pong_width - 20, pong_height // 2 - paddle_height // 2, paddle_width, paddle_height)
ball = pygame.Rect(pong_width // 2 - 7, pong_height // 2 - 7, 14, 14)
# Velocidades duplicadas
ball_speed_x, ball_speed_y = 15, 15

CounterPlr = 0
CounterAI = 0

# Efectos de partículas
particle_effects = []
ball_trail = BallTrail(NEON_GREEN)
score_effects = []

def update_game_state():
    global CounterPlr, CounterAI, ball_speed_x, ball_speed_y
    global particle_effects, ball_trail, score_effects
    
    # Actualizar posición de la pelota
    ball.x += ball_speed_x
    ball.y += ball_speed_y
    
    # Actualizar trail de la pelota
    ball_trail.add_position(ball.centerx, ball.centery)

    # Rebote en techo y piso
    if ball.top <= 0:
        ball.top = 0
        ball_speed_y = abs(ball_speed_y)
        if WALL_HIT:
            WALL_HIT.play()
        particle_effects.append(CollisionEffect(ball.centerx, ball.top, NEON_GREEN))
    elif ball.bottom >= pong_height:
        ball.bottom = pong_height
        ball_speed_y = -abs(ball_speed_y)
        if WALL_HIT:
            WALL_HIT.play()
        particle_effects.append(CollisionEffect(ball.centerx, ball.bottom, NEON_GREEN))

    # Rebote en las paletas
    if ball.colliderect(player_paddle):
        # Evitar que la pelota se "pegue" a la paleta
        ball.left = player_paddle.right
        
        # Calcular el punto de impacto relativo (-1 a 1)
        relative_intersect_y = (ball.centery - player_paddle.centery) / (paddle_height/2)
        
        # Aumentar velocidad gradualmente
        ball_speed_x = abs(ball_speed_x) * 1.1
        
        # Ajustar el ángulo basado en dónde golpea la paleta
        ball_speed_y = relative_intersect_y * (pong_height * 0.02)
        
        # Añadir variación al rebote
        ball_speed_y += random.uniform(-2, 2)
        
        if PADDLE_HIT:
            PADDLE_HIT.play()
        particle_effects.append(CollisionEffect(ball.left, ball.centery, NEON_BLUE))
        
    elif ball.colliderect(ai_paddle):
        # Evitar que la pelota se "pegue" a la paleta
        ball.right = ai_paddle.left
        
        # Calcular el punto de impacto relativo (-1 a 1)
        relative_intersect_y = (ball.centery - ai_paddle.centery) / (paddle_height/2)
        
        # Aumentar velocidad gradualmente
        ball_speed_x = -abs(ball_speed_x) * 1.1
        
        # Ajustar el ángulo basado en dónde golpea la paleta
        ball_speed_y = relative_intersect_y * (pong_height * 0.02)
        
        # Añadir variación al rebote
        ball_speed_y += random.uniform(-2, 2)
        
        if PADDLE_HIT:
            PADDLE_HIT.play()
        particle_effects.append(CollisionEffect(ball.right, ball.centery, NEON_PINK))

    # Actualizar IA
    ai_controller.update(ball, ball_speed_x, ball_speed_y)

    # Puntuación
    if ball.left <= 0:
        ball.center = (pong_width // 2, pong_height // 2)
        ball_speed_x = abs(pong_width * 0.015)
        ball_speed_y = random.uniform(-pong_height * 0.012, pong_height * 0.012)
        CounterAI += 1
        if SCORE_SOUND:
            SCORE_SOUND.play()
        score_effects.append(ScoreFlash(3*pong_width//4, pong_height//3, CounterAI, NEON_PINK))
        particle_effects.append(CollisionEffect(0, ball.centery, NEON_PURPLE))
        
    elif ball.right >= pong_width:
        ball.center = (pong_width // 2, pong_height // 2)
        ball_speed_x = -abs(pong_width * 0.015)
        ball_speed_y = random.uniform(-pong_height * 0.012, pong_height * 0.012)
        CounterPlr += 1
        if SCORE_SOUND:
            SCORE_SOUND.play()
        score_effects.append(ScoreFlash(pong_width//4, pong_height//3, CounterPlr, NEON_BLUE))
        particle_effects.append(CollisionEffect(pong_width, ball.centery, NEON_PURPLE))
    
    # Mantener la velocidad de la pelota en un rango razonable
    max_speed_x = pong_width * 0.025
    max_speed_y = pong_height * 0.02
    ball_speed_x = pygame.math.clamp(ball_speed_x, -max_speed_x, max_speed_x)
    ball_speed_y = pygame.math.clamp(ball_speed_y, -max_speed_y, max_speed_y)

def draw_game():
    global CounterPlr, CounterAI
    
    # Dibujar el fondo del área de juego con un gradiente
    background = pygame.Surface((pong_width, pong_height))
    for y in range(0, pong_height, 4):
        alpha = 255 - int((y / pong_height) * 100)
        pygame.draw.rect(background, (*BACKGROUND_COLOR, alpha),
                        (0, y, pong_width, 4))
    screen.blit(background, (cam_width, 0))
    
    # Dibujar cuadrícula de fondo
    for x in range(0, pong_width, 40):
        pygame.draw.line(screen, GRID_COLOR, 
                        (cam_width + x, 0),
                        (cam_width + x, pong_height), 1)
    for y in range(0, pong_height, 40):
        pygame.draw.line(screen, GRID_COLOR,
                        (cam_width, y),
                        (cam_width + pong_width, y), 1)
    
    # Dibujar línea central punteada
    for y in range(0, pong_height, 20):
        pygame.draw.rect(screen, (50, 50, 80),
                        (cam_width + pong_width//2 - 2, y, 4, 10))
    
    # Dibujar paletas con efectos de brillo
    pygame.draw.rect(screen, NEON_BLUE,
                     (player_paddle.x + cam_width - 2, player_paddle.y - 2,
                      player_paddle.width + 4, player_paddle.height + 4))
    pygame.draw.rect(screen, WHITE,
                     (player_paddle.x + cam_width, player_paddle.y,
                      player_paddle.width, player_paddle.height))
    
    pygame.draw.rect(screen, NEON_PINK,
                     (ai_paddle.x + cam_width - 2, ai_paddle.y - 2,
                      ai_paddle.width + 4, ai_paddle.height + 4))
    pygame.draw.rect(screen, WHITE,
                     (ai_paddle.x + cam_width, ai_paddle.y,
                      ai_paddle.width, ai_paddle.height))
    
    # Dibujar la bola con efecto de brillo
    ball_glow = pygame.Surface((ball.width + 8, ball.height + 8), pygame.SRCALPHA)
    pygame.draw.circle(ball_glow, (*NEON_GREEN, 128),
                      (ball.width//2 + 4, ball.height//2 + 4), ball.width//2 + 4)
    screen.blit(ball_glow, (ball.x + cam_width - 4, ball.y - 4))
    
    pygame.draw.circle(screen, NEON_GREEN,
                      (ball.x + cam_width + ball.width//2,
                       ball.y + ball.height//2), ball.width//2)
    pygame.draw.circle(screen, WHITE,
                      (ball.x + cam_width + ball.width//2,
                       ball.y + ball.height//2), ball.width//2 - 2)

    # Dibujar puntuación con estilo moderno
    font = pygame.font.Font(None, 80)
    
    # Puntuación del jugador
    plr_score = font.render(str(CounterPlr), True, NEON_BLUE)
    plr_rect = plr_score.get_rect(center=(cam_width + pong_width//4, 50))
    screen.blit(plr_score, plr_rect)
    
    # Puntuación de la IA
    ai_score = font.render(str(CounterAI), True, NEON_PINK)
    ai_rect = ai_score.get_rect(center=(cam_width + 3*pong_width//4, 50))
    screen.blit(ai_score, ai_rect)
    
    # Dibujar "VS" en el centro
    vs_font = pygame.font.Font(None, 40)
    vs_text = vs_font.render("VS", True, (150, 150, 150))
    vs_rect = vs_text.get_rect(center=(cam_width + pong_width//2, 50))
    screen.blit(vs_text, vs_rect)
    

# -----------------------------
# CONFIGURACIÓN DE MEDIAPIPE PARA HAND TRACKING
# -----------------------------
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False,
                       max_num_hands=1,
                       min_detection_confidence=0.7,
                       min_tracking_confidence=0.5)


cap = cv2.VideoCapture(0)

def get_hand_y():
    """
    Captura un frame desde la webcam, lo procesa con MediaPipe y
    retorna la coordenada Y normalizada (0 a 1) del dedo índice (landmark 8).
    Si no se detecta una mano, retorna None.
    """
    ret, frame = cap.read()
    if not ret:
        return None
    frame = cv2.flip(frame, 1)  # Modo espejo
    results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    
    # Dibujar landmarks de la mano
    frame = draw_hand_landmarks(frame, results)
    
    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]
        return hand_landmarks.landmark[8].y  # Coordenada Y normalizada
    return None

def draw_hand_landmarks(frame, results):
    """
    Dibuja los landmarks y conexiones de la mano en el frame
    """
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Dibujar conexiones con estilo personalizado
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style())
    return frame

def frame_to_pygame_surface(frame, target_width, target_height):
    """
    Convierte un frame de OpenCV a una superficie de Pygame
    """
    frame = cv2.resize(frame, (target_width, target_height))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = np.rot90(frame)
    frame = pygame.surfarray.make_surface(frame)
    frame = pygame.transform.flip(frame, True, False)
    return frame

# -----------------------------
# BUCLE PRINCIPAL
# -----------------------------
running = True
hand_last_seen = time.time()
game_paused = False
PAUSE_MSG = "Detectando mano..."

# Inicialización de efectos visuales
particle_effects = []
score_effects = []
ball_trail = BallTrail(NEON_GREEN)
paddle_trail = Trail(NEON_BLUE)

# Inicializar el controlador de la IA con parámetros más agresivos
class AIController:
    def __init__(self):
        self.target_y = pong_height // 2
        self.current_velocity = 0
        self.max_speed = pong_height * 0.03  # Velocidad máxima aumentada
        self.acceleration = pong_height * 0.003  # Aceleración aumentada
        self.deceleration = 0.85  # Factor de desaceleración más suave
        self.prediction_factor = 1.0
        self.reaction_delay = []
        self.max_reaction_frames = 2
        self.last_predictions = []
        self.prediction_window = 3  # Ventana de predicción más pequeña para respuestas más rápidas
        self.difficulty_factor = 0.98  # IA más precisa
        self.anticipation_factor = 1.2  # Factor de anticipación aumentado
        
    def predict_ball_position(self, ball_rect, ball_speed_x, ball_speed_y):
        if ball_speed_x <= 0:
            # Posicionamiento más inteligente cuando la pelota va hacia el jugador
            return pong_height // 2 + (ball_speed_y * 5)
            
        # Calcular tiempo hasta interceptar
        time_to_intercept = (ai_paddle.centerx - ball_rect.centerx) / ball_speed_x
        
        # Predicción básica
        predicted_y = ball_rect.centery + (ball_speed_y * time_to_intercept * self.anticipation_factor)
        
        # Ajustar por rebotes
        while predicted_y < 0 or predicted_y > pong_height:
            if predicted_y < 0:
                predicted_y = -predicted_y
            if predicted_y > pong_height:
                predicted_y = 2 * pong_height - predicted_y
        
        # Añadir pequeña variación para hacer la IA más humana
        if time_to_intercept > 20:  # Solo añadir error cuando la pelota está lejos
            prediction_error = random.randint(
                -int(paddle_height * 0.1 * (1 - self.difficulty_factor)),
                int(paddle_height * 0.1 * (1 - self.difficulty_factor))
            )
            predicted_y += prediction_error
        
        # Suavizar predicción
        self.last_predictions.append(predicted_y)
        if len(self.last_predictions) > self.prediction_window:
            self.last_predictions.pop(0)
        
        smoothed_prediction = sum(self.last_predictions) / len(self.last_predictions)
        return pygame.math.clamp(smoothed_prediction, paddle_height//2, pong_height - paddle_height//2)
        
    def update(self, ball_rect, ball_speed_x, ball_speed_y):
        # Obtener posición objetivo
        predicted_y = self.predict_ball_position(ball_rect, ball_speed_x, ball_speed_y)
        
        # Calcular distancia a la pelota
        distance_to_ball = abs(ai_paddle.centerx - ball_rect.centerx)
        distance_factor = min(1.0, distance_to_ball / (pong_width * 0.3))
        
        # Ajustar predicción basada en la velocidad de la pelota
        if abs(ball_speed_y) > pong_height * 0.01:
            predicted_y += ball_speed_y * 3 * distance_factor
        
        # Actualizar target con suavizado
        self.target_y = predicted_y
        
        # Calcular distancia al objetivo
        distance_to_target = self.target_y - ai_paddle.centery
        
        # Zona muerta adaptativa
        dead_zone = paddle_height * 0.05
        
        # Actualizar velocidad con movimiento más fluido
        if abs(distance_to_target) > dead_zone:
            # Calcular dirección deseada
            direction = 1 if distance_to_target > 0 else -1
            
            # Acelerar más suavemente
            target_speed = self.max_speed * min(1.0, abs(distance_to_target) / (paddle_height * 2))
            
            # Aplicar aceleración con más control
            if direction > 0:
                if self.current_velocity < target_speed:
                    self.current_velocity += self.acceleration
            else:
                if self.current_velocity > -target_speed:
                    self.current_velocity -= self.acceleration
        else:
            # Desacelerar más suavemente
            self.current_velocity *= self.deceleration
        
        # Limitar velocidad máxima
        self.current_velocity = pygame.math.clamp(
            self.current_velocity,
            -self.max_speed,
            self.max_speed
        )
        
        # Actualizar posición
        ai_paddle.y += self.current_velocity
        
        # Mantener la paleta dentro de los límites
        ai_paddle.clamp_ip(pygame.Rect(0, 0, pong_width, pong_height))

# Inicializar el controlador de la IA
ai_controller = AIController()

show_instructions()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:  # Salir con ESC
                running = False

    hand_y = get_hand_y()
    if hand_y is not None:
        hand_last_seen = time.time()
        if game_paused:
            game_paused = False
        new_y = int(hand_y * (pong_height - paddle_height))
        player_paddle.y = new_y
        paddle_trail.add_position(player_paddle.centerx, player_paddle.centery)
    else:
        if time.time() - hand_last_seen > 0.5:
            game_paused = True

    ret, cam_frame = cap.read()
    if ret:
        cam_frame = cv2.flip(cam_frame, 1)
        results = hands.process(cv2.cvtColor(cam_frame, cv2.COLOR_BGR2RGB))
        cam_frame = draw_hand_landmarks(cam_frame, results)
        cam_surface = frame_to_pygame_surface(cam_frame, cam_width, cam_height)
        screen.blit(cam_surface, (0, 0))

    draw_game()

    if game_paused:
        font = pygame.font.Font(None, 60)
        text = font.render(PAUSE_MSG, True, NEON_PURPLE)
        text_rect = text.get_rect(center=(cam_width + pong_width // 2, pong_height // 2))
        screen.blit(text, text_rect)
        pygame.display.flip()
        clock.tick(60)
        continue

    ball_trail.draw(screen, cam_width)
    paddle_trail.draw(screen)
    
    particle_effects = [effect for effect in particle_effects 
                       if effect.update_and_draw(screen, cam_width)]
    
    score_effects = [effect for effect in score_effects 
                    if effect.update_and_draw(screen, cam_width)]

    if not game_paused:
        update_game_state()

    pygame.display.flip()
    clock.tick(60)

# Limpieza de recursos
cap.release()
hands.close()
pygame.quit()
sys.exit()
