import cv2
import mediapipe as mp
import math
import serial
import time
import random

# Configuración de puerto serial
try:
    microbit_port = '/dev/tty.usbmodem11402'  # Cambiar según el puerto correspondiente
    microbit = serial.Serial(microbit_port, 115200, timeout=1)
    print(f"Conexión con micro:bit en {microbit_port} exitosa.")
    time.sleep(2)
except serial.SerialException:
    print(f"Error: No se pudo conectar con la micro:bit en el puerto {microbit_port}.")
    print("El programa continuará sin enviar comandos al robot.")
    microbit = None

# Variables de control
last_sent_gesture = None
last_detected_gesture = None
COMMAND_COOLDOWN = 1
last_command_time = 0
FRAME_SKIP = 2
frame_count = 0

# Puntuación
human_score = 0
robot_score = 0

# Inicializar Mediapipe
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

def calculate_distance(point1, point2):
    return math.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2)

def count_fingers(hand_landmarks, hand_label):
    tips_ids = [4, 8, 12, 16, 20]
    fingers = []

    if hand_label == 'Right':
        if hand_landmarks.landmark[tips_ids[0]].x < hand_landmarks.landmark[tips_ids[0] - 1].x:
            fingers.append(1)
        else:
            fingers.append(0)
    else:
        if hand_landmarks.landmark[tips_ids[0]].x > hand_landmarks.landmark[tips_ids[0] - 1].x:
            fingers.append(1)
        else:
            fingers.append(0)

    for id in range(1, 5):
        if hand_landmarks.landmark[tips_ids[id]].y < hand_landmarks.landmark[tips_ids[id] - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)

    return fingers

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
    return None

def enviar_comando_a_robot(movimiento_humano):
    global microbit, robot_score, human_score

    if not microbit:
        return None

    decision_robot = ""
    if movimiento_humano.lower() == "piedra":
        decision_robot = "papel"
    elif movimiento_humano.lower() == "papel":
        decision_robot = "tijera"
    elif movimiento_humano.lower() == "tijera":
        decision_robot = "piedra"

    if decision_robot:
        print(f"Humano jugó: {movimiento_humano}. Enviando comando al robot: '{decision_robot}'")
        microbit.write(f"{decision_robot}\n".encode('utf-8'))

        # Actualizar marcador
        if decision_robot == "papel" and movimiento_humano.lower() == "piedra":
            robot_score += 1
        elif decision_robot == "tijera" and movimiento_humano.lower() == "papel":
            robot_score += 1
        elif decision_robot == "piedra" and movimiento_humano.lower() == "tijera":
            robot_score += 1
        else:
            human_score += 1

    return decision_robot

# Configuración de cámara y Mediapipe
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

cap = cv2.VideoCapture(0)

try:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            continue

        frame_count += 1
        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        current_time = time.time()

        if frame_count % FRAME_SKIP == 0:
            results = hands.process(image_rgb)

            if results.multi_hand_landmarks:
                for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    hand_label = handedness.classification[0].label
                    mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    fingers = count_fingers(hand_landmarks, hand_label)
                    gesture = detect_gesture(fingers, hand_landmarks)

                    if gesture:
                        last_detected_gesture = gesture

                        if (gesture != last_sent_gesture) or (current_time - last_command_time > COMMAND_COOLDOWN):
                            enviar_comando_a_robot(gesture)
                            last_sent_gesture = gesture
                            last_command_time = current_time

            else:
                last_detected_gesture = None

        # Mostrar siempre el último gesto detectado
        if last_detected_gesture:
            color = (0, 255, 0) if last_detected_gesture == "Piedra" else (255, 0, 0) if last_detected_gesture == "Papel" else (0, 0, 255)
            cv2.putText(image, last_detected_gesture, (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 2, color, 4)

        # Mostrar estado del juego
        if current_time - last_command_time < COMMAND_COOLDOWN:
            texto_estado = "Robot jugando... Espera"
        else:
            texto_estado = "Muestra tu mano!"

        cv2.putText(image, texto_estado, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

        # Mostrar puntuación
        cv2.putText(image, f"Humano: {human_score}", (10, 400), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)
        cv2.putText(image, f"Robot: {robot_score}", (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)

        cv2.imshow('Detector de Piedra, Papel o Tijera', image)

        if cv2.waitKey(5) & 0xFF == 27:  # Presionar 'Esc' para salir
            break
finally:
    hands.close()
    cap.release()
    cv2.destroyAllWindows()
    if microbit:
        microbit.close()
        print("Conexión con micro:bit cerrada.")