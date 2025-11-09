import pygame
import sys
import os
import random
import cv2
import mediapipe as mp
import numpy as np

pygame.init()

# Pantalla completa y dimensiones dinámicas
SCREEN = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = SCREEN.get_size()
CAMERA_WIDTH, CAMERA_HEIGHT = 480, 360  # Tamaño del recuadro de la cámara (más grande)

# Función para escalar imágenes un 10%
def scale_img(img, factor=1.2):
    size = img.get_size()
    return pygame.transform.scale(img, (int(size[0]*factor), int(size[1]*factor)))

def scale_img_list(img_list, factor=1.2):
    return [scale_img(img, factor) for img in img_list]

# Cargar imágenes del juego y ESCALAR
RUNNING = scale_img_list([
    pygame.image.load(os.path.join("Games", "Assets_Dino", "Dino", "DinoRun1.png")),
    pygame.image.load(os.path.join("Games", "Assets_Dino", "Dino", "DinoRun2.png"))
])
JUMPING = scale_img(pygame.image.load(os.path.join("Games", "Assets_Dino", "Dino", "DinoJump.png")))
DUCKING = scale_img_list([
    pygame.image.load(os.path.join("Games", "Assets_Dino", "Dino", "DinoDuck1.png")),
    pygame.image.load(os.path.join("Games", "Assets_Dino", "Dino", "DinoDuck2.png"))
])

SMALL_CACTUS = scale_img_list([
    pygame.image.load(os.path.join("Games", "Assets_Dino", "Cactus", "SmallCactus1.png")),
    pygame.image.load(os.path.join("Games", "Assets_Dino", "Cactus", "SmallCactus2.png")),
    pygame.image.load(os.path.join("Games", "Assets_Dino", "Cactus", "SmallCactus3.png"))
])
LARGE_CACTUS = scale_img_list([
    pygame.image.load(os.path.join("Games", "Assets_Dino", "Cactus", "LargeCactus1.png")),
    pygame.image.load(os.path.join("Games", "Assets_Dino", "Cactus", "LargeCactus2.png")),
    pygame.image.load(os.path.join("Games", "Assets_Dino", "Cactus", "LargeCactus3.png"))
])

BIRD = scale_img_list([
    pygame.image.load(os.path.join("Games", "Assets_Dino", "Bird", "Bird1.png")),
    pygame.image.load(os.path.join("Games", "Assets_Dino", "Bird", "Bird2.png"))
])

CLOUD = pygame.image.load(os.path.join("Games", "Assets_Dino", "Other", "Cloud.png"))
BG = pygame.image.load(os.path.join("Games", "Assets_Dino", "Other", "Track.png"))

# Inicialización de MediaPipe para seguimiento de manos
mp_hands = mp.solutions.hands
hands_detector = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Inicializamos la cámara (única para el juego)
cap = cv2.VideoCapture(0)

def detect_thumbs_up(hand_landmarks):
    """Detecta si la mano está haciendo un gesto de pulgar arriba"""
    if not hand_landmarks:
        return False
    thumb_tip = hand_landmarks.landmark[4]
    thumb_mcp = hand_landmarks.landmark[2]
    index_tip = hand_landmarks.landmark[8]
    middle_tip = hand_landmarks.landmark[12]
    ring_tip = hand_landmarks.landmark[16]
    pinky_tip = hand_landmarks.landmark[20]
    thumbs_up = (thumb_tip.y < thumb_mcp.y and
                 all(f.y > thumb_mcp.y for f in [index_tip, middle_tip, ring_tip, pinky_tip]))
    return thumbs_up

def draw_rounded_rect(surface, color, rect, radius):
    pygame.draw.rect(surface, color, rect, border_radius=radius)

def show_instructions():
    """Muestra la mini-UI de instrucciones y espera pulgar arriba para comenzar"""
    instructions = [
        ("\u00a1Bienvenido a Dinosaur!", 40, (255, 255, 255)),
        ("Controla al dinosaurio con tu mano", 28, (200, 200, 200)),
        ("", 20, (255, 255, 255)),
        ("C\u00f3mo jugar:", 32, (255, 255, 255)),
        ("\u2022 Coloca el dedo \u00edndice por encima de la l\u00ednea verde para saltar", 24, (200, 200, 200)),
        ("\u2022 Coloca el dedo \u00edndice por debajo de la l\u00ednea roja para agacharte", 24, (200, 200, 200)),
        ("", 20, (255, 255, 255)),
        ("Haz un pulgar arriba para comenzar", 32, (98, 212, 155))
    ]

    waiting = True
    popup_alpha = 0
    clock_local = pygame.time.Clock()
    while waiting:
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands_detector.process(frame_rgb)

        frame_rgb = cv2.resize(frame_rgb, (SCREEN_WIDTH, SCREEN_HEIGHT))
        cam_surface = pygame.surfarray.make_surface(np.rot90(frame_rgb))
        cam_surface = pygame.transform.flip(cam_surface, True, False)

        SCREEN.fill((255, 255, 255))
        SCREEN.blit(cam_surface, (0, 0))

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        SCREEN.blit(overlay, (0, 0))

        if popup_alpha < 230:
            popup_alpha += 8

        popup_w, popup_h = 800, 360
        popup_x = (SCREEN_WIDTH - popup_w) // 2
        popup_y = (SCREEN_HEIGHT - popup_h) // 2
        popup = pygame.Surface((popup_w, popup_h), pygame.SRCALPHA)
        draw_rounded_rect(popup, (30, 30, 40, min(240, popup_alpha)), pygame.Rect(0, 0, popup_w, popup_h), 20)

        y_off = 30
        for text, size, color in instructions:
            font = pygame.font.Font(None, size)
            s = font.render(text, True, (*color, min(255, popup_alpha)))
            r = s.get_rect(center=(popup_w//2, y_off))
            popup.blit(s, r)
            y_off += size + 8

        SCREEN.blit(popup, (popup_x, popup_y))

        if results.multi_hand_landmarks:
            if detect_thumbs_up(results.multi_hand_landmarks[0]):
                pygame.display.flip()
                pygame.time.wait(400)
                waiting = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        pygame.display.flip()
        clock_local.tick(30)


class Dinosaur:
    X_POS = 80
    Y_POS = int(SCREEN_HEIGHT * 0.60)  # Más abajo
    Y_POS_DUCK = int(SCREEN_HEIGHT * 0.67)  # Más abajo
    JUMP_VEL = 8.5

    def __init__(self):
        self.duck_img = DUCKING
        self.run_img = RUNNING
        self.jump_img = JUMPING

        self.dino_duck = False
        self.dino_run = True
        self.dino_jump = False

        self.step_index = 0
        self.jump_vel = self.JUMP_VEL
        self.image = self.run_img[0]
        self.dino_rect = self.image.get_rect()
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS

    def update(self, userInput):
        if self.dino_duck:
            self.duck()
        if self.dino_run:
            self.run()
        if self.dino_jump:
            self.jump()

        if self.step_index >= 10:
            self.step_index = 0

        if userInput[pygame.K_UP] and not self.dino_jump:
            self.dino_duck = False
            self.dino_run = False
            self.dino_jump = True
        elif userInput[pygame.K_DOWN] and not self.dino_jump:
            self.dino_duck = True
            self.dino_run = False
            self.dino_jump = False
        elif not (self.dino_jump or userInput[pygame.K_DOWN]):
            self.dino_duck = False
            self.dino_run = True
            self.dino_jump = False

    def duck(self):
        self.image = self.duck_img[self.step_index // 5]
        self.dino_rect = self.image.get_rect()
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS_DUCK
        self.step_index += 1

    def run(self):
        self.image = self.run_img[self.step_index // 5]
        self.dino_rect = self.image.get_rect()
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS
        self.step_index += 1

    def jump(self):
        self.image = self.jump_img
        if self.dino_jump:
            self.dino_rect.y -= self.jump_vel * 4
            self.jump_vel -= 0.8
        if self.jump_vel < -self.JUMP_VEL:
            self.dino_jump = False
            self.jump_vel = self.JUMP_VEL

    def draw(self, SCREEN):
        SCREEN.blit(self.image, (self.dino_rect.x, self.dino_rect.y))

class Cloud:
    def __init__(self):
        self.x = SCREEN_WIDTH + random.randint(800, 2000)
        self.y = random.randint(int(SCREEN_HEIGHT * 0.10), int(SCREEN_HEIGHT * 0.40))
        self.image = CLOUD
        self.width = self.image.get_width()

    def update(self):
        self.x -= game_speed * 0.5
        if self.x < -self.width:
            self.x = SCREEN_WIDTH + random.randint(800, 2000)
            self.y = random.randint(int(SCREEN_HEIGHT * 0.10), int(SCREEN_HEIGHT * 0.40))

    def draw(self, SCREEN):
        SCREEN.blit(self.image, (self.x, self.y))

class Obstacle:
    def __init__(self, image, type):
        self.image = image
        self.type = type
        self.rect = self.image[self.type].get_rect()
        self.rect.x = SCREEN_WIDTH

    def update(self):
        self.rect.x -= game_speed
        if self.rect.x < -self.rect.width:
            obstacles.pop(0)

    def draw(self, SCREEN):
        SCREEN.blit(self.image[self.type], self.rect)

class SmallCactus(Obstacle):
    def __init__(self, image):
        self.type = random.randint(0, 2)
        super().__init__(image, self.type)
        self.rect.y = int(SCREEN_HEIGHT * 0.63)  # Más abajo

class LargeCactus(Obstacle):
    def __init__(self, image):
        self.type = random.randint(0, 2)
        super().__init__(image, self.type)
        self.rect.y = int(SCREEN_HEIGHT * 0.60)  # Más abajo

class Bird(Obstacle):
    def __init__(self, image):
        self.type = 0
        super().__init__(image, self.type)
        self.rect.y = int(SCREEN_HEIGHT * 0.53)  # Más abajo
        self.index = 0

    def draw(self, SCREEN):
        if self.index >= 9:
            self.index = 0
        SCREEN.blit(self.image[self.index // 5], self.rect)
        self.index += 1

def get_hand_action():
    ret, frame = cap.read()
    if not ret:
        return "run", None, False
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands_detector.process(rgb)
    h, w, _ = frame.shape
    detected = False
    if results.multi_hand_landmarks:
        detected = True
        handLms = results.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)
        index_finger_tip = handLms.landmark[8]
        cx, cy = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
        cv2.circle(frame, (cx, cy), 8, (255, 0, 0), -1)
        finger_y = index_finger_tip.y * SCREEN_HEIGHT
        if finger_y < SCREEN_HEIGHT / 3:
            action = "jump"
        elif finger_y > 2 * SCREEN_HEIGHT / 3:
            action = "duck"
        else:
            action = "run"
    else:
        action = "run"
    # Dibujar las líneas de referencia en el frame
    cv2.line(frame, (0, int(h/3)), (w, int(h/3)), (0, 255, 0), 2)   # Línea superior (salto)
    cv2.line(frame, (0, int(2*h/3)), (w, int(2*h/3)), (0, 0, 255), 2) # Línea inferior (agacharse)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_rgb = np.rot90(frame_rgb)
    cam_surface = pygame.surfarray.make_surface(frame_rgb)
    return action, cam_surface, detected

def score():
    global points, game_speed
    points += 1
    if points % 150 == 0:
        game_speed += 0.5
    text = font.render("Points: " + str(points), True, (0, 0, 0))
    textRect = text.get_rect(center=(80, 40))
    SCREEN.blit(text, textRect)

def background():
    global x_pos_bg, y_pos_bg
    image_width = BG.get_width()
    bg_y = int(SCREEN_HEIGHT * 0.7)  # Más abajo
    SCREEN.blit(BG, (x_pos_bg, bg_y))
    SCREEN.blit(BG, (image_width + x_pos_bg, bg_y))
    if x_pos_bg <= -image_width:
        x_pos_bg = 0
    x_pos_bg -= game_speed

def game_over_screen():
    over_font = pygame.font.Font('freesansbold.ttf', 50)
    over_text = over_font.render("GAME OVER", True, (255, 0, 0))
    over_rect = over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    SCREEN.blit(over_text, over_rect)
    pygame.display.update()
    pygame.time.delay(2000)

def main():
    global game_speed, x_pos_bg, y_pos_bg, points, obstacles, font, BG
    run_game = True
    clock = pygame.time.Clock()
    player = Dinosaur()
    # Crear varias nubes
    clouds = [Cloud() for _ in range(6)]
    game_speed = 17.5
    x_pos_bg = 0
    y_pos_bg = 380
    points = 0
    font = pygame.font.Font('freesansbold.ttf', 20)
    obstacles = []
    death = False

    last_hand_time = pygame.time.get_ticks()
    paused = False

    while run_game:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run_game = False
                pygame.quit()
                return

        hand_action, cam_surface, detected = get_hand_action()
        if detected:
            last_hand_time = pygame.time.get_ticks()
            if paused:
                paused = False
        else:
            if pygame.time.get_ticks() - last_hand_time > 500:
                paused = True

        if paused:
            
            pause_font = pygame.font.Font('freesansbold.ttf', 50)
            pause_text = pause_font.render("Detectando mano...", True, (0, 0, 0))
            pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            SCREEN.blit(pause_text, pause_rect)
            if cam_surface is not None:
                cam_surface = pygame.transform.scale(cam_surface, (CAMERA_WIDTH, CAMERA_HEIGHT))
                SCREEN.blit(cam_surface, (SCREEN_WIDTH - CAMERA_WIDTH, 0))
            pygame.display.update()
            clock.tick(15)
            continue

        userInput = {pygame.K_UP: hand_action == "jump", pygame.K_DOWN: hand_action == "duck"}

        SCREEN.fill((255, 255, 255))
        
        player.draw(SCREEN)
        player.update(userInput)

        if len(obstacles) == 0:
            r = random.randint(0, 2)
            if r == 0:
                obstacles.append(SmallCactus(SMALL_CACTUS))
            elif r == 1:
                obstacles.append(LargeCactus(LARGE_CACTUS))
            else:
                obstacles.append(Bird(BIRD))
                
        # Comprobación de colisiones con hitboxes reducidas
        for obstacle in obstacles:
            obstacle.draw(SCREEN)
            obstacle.update()
            dino_hitbox = player.dino_rect.inflate(-20, -20)
            # Para las aves, se reduce la hitbox y se desplaza 10 píxeles hacia abajo
            if isinstance(obstacle, Bird):
                obstacle_hitbox = obstacle.rect.inflate(-10, -10)
                obstacle_hitbox.y += 10
            else:
                obstacle_hitbox = obstacle.rect.inflate(-10, -10)
            if dino_hitbox.colliderect(obstacle_hitbox):
                death = True

        background()
        # Dibujar y actualizar todas las nubes
        for cloud in clouds:
            cloud.draw(SCREEN)
            cloud.update()
        score()

        if cam_surface is not None:
            cam_surface = pygame.transform.scale(cam_surface, (CAMERA_WIDTH, CAMERA_HEIGHT))
            SCREEN.blit(cam_surface, (SCREEN_WIDTH - CAMERA_WIDTH, 0))

        pygame.display.update()
        clock.tick(30)

        if death:
            game_over_screen()
            run_game = False

while True:
    # Mostrar instrucciones antes de iniciar la partida
    try:
        show_instructions()
    except Exception:
        pass
    main()
