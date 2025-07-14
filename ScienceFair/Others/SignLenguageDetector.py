import cv2
import mediapipe as mp
import math

# Inicializar MediaPipe y herramientas de dibujo
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

def calculate_distance(point1, point2):
    """Calcula la distancia euclidiana entre dos puntos."""
    return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)

def detect_sign_lsc(fingers, hand_landmarks):
    """
    Función para detectar una letra (o signo) de la Lengua de Señas Costarricense (LSC)
    utilizando heurísticas basadas en la cantidad de dedos extendidos y distancias.
    NOTA: Estas reglas son aproximadas y deben ajustarse y ampliarse con base en datos
    reales de LSC.
    """
    count = sum(fingers)
    thumb_tip   = hand_landmarks.landmark[4]
    index_tip   = hand_landmarks.landmark[8]
    middle_tip  = hand_landmarks.landmark[12]
    ring_tip    = hand_landmarks.landmark[16]
    pinky_tip   = hand_landmarks.landmark[20]
    wrist       = hand_landmarks.landmark[0]
    index_mcp   = hand_landmarks.landmark[5]
    middle_mcp  = hand_landmarks.landmark[9]

    # ---------------------
    # Ejemplo para 0 dedos extendidos (posibles: A, E, etc.)
    if count == 0:
        dist_thumb_index = calculate_distance(thumb_tip, index_mcp)
        # Para LSC podríamos asumir que un puño cerrado con pulgar cerca corresponde a "A"
        if dist_thumb_index < 0.035:
            return "A"
        else:
            return "E"

    # ---------------------
    # Ejemplo para 1 dedo extendido (posibles: D, X, I)
    if count == 1:
        # Si solo el índice está extendido
        if fingers[1] == 1:
            index_pip = hand_landmarks.landmark[6]
            # Si el dedo presenta una curvatura pronunciada se interpreta como "X"
            if abs(index_tip.y - index_pip.y) > 0.03:
                return "X"
            else:
                return "D"
        # Si solo el meñique está extendido se interpreta como "I"
        if fingers[4] == 1:
            return "I"

    # ---------------------
    # Ejemplo para 2 dedos extendidos (posibles: L, Y, U, H, V, G, Q, R)
    if count == 2:
        # L: pulgar e índice extendidos
        if fingers[0] == 1 and fingers[1] == 1:
            return "L"
        # Y: pulgar y meñique extendidos
        if fingers[0] == 1 and fingers[4] == 1:
            return "Y"
        # Índice y medio extendidos
        if fingers[1] == 1 and fingers[2] == 1:
            dist = calculate_distance(index_tip, middle_tip)
            if dist < 0.045:
                return "U"
            else:
                if abs(index_tip.y - middle_tip.y) < 0.025:
                    return "H"
                else:
                    return "V"
        # Regla arbitraria para otras combinaciones (G, Q, R)
        if fingers[0] == 1 and fingers[2] == 1:
            return "G"
        if fingers[0] == 1 and fingers[3] == 1:
            return "Q"
        if fingers[1] == 1 and fingers[4] == 1:
            return "R"

    # ---------------------
    # Ejemplo para 3 dedos extendidos (posibles: W, K, P)
    if count == 3:
        # W: índice, medio y anular extendidos
        if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1:
            return "W"
        # K: pulgar, índice y medio extendidos
        if fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 1:
            return "K"
        # Si no se cumple lo anterior, se puede interpretar como "P"
        return "P"

    # ---------------------
    # Ejemplo para 4 dedos extendidos (posibles: C, O)
    if count == 4:
        avg_distance = (calculate_distance(wrist, index_tip) +
                        calculate_distance(wrist, middle_tip) +
                        calculate_distance(wrist, ring_tip) +
                        calculate_distance(wrist, pinky_tip)) / 4
        if fingers[0] == 0 and avg_distance < 0.25:
            return "C"
        else:
            return "O"

    # ---------------------
    # Ejemplo para 5 dedos extendidos (posibles: B u O)
    if count == 5:
        avg_distance = (calculate_distance(wrist, index_tip) +
                        calculate_distance(wrist, middle_tip) +
                        calculate_distance(wrist, ring_tip) +
                        calculate_distance(wrist, pinky_tip)) / 4
        if avg_distance > 0.3:
            return "B"
        else:
            return "O"

    # Se pueden agregar reglas adicionales para letras propias de LSC (por ejemplo, "Ñ")
    return ""

# Configurar MediaPipe Hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

# Variables para formar la oración
sentence = ""
current_sign = ""

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Voltear la imagen y convertir a RGB para MediaPipe
    frame = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
    results = hands.process(frame)
    # Convertir de nuevo a BGR para mostrar en OpenCV
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    height, width, _ = frame.shape

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Dibujar los landmarks y conexiones
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            # Detectar dedos extendidos
            fingers = []
            tips_ids = [4, 8, 12, 16, 20]
            # Pulgar: para mano derecha se utiliza una heurística de comparación en x
            if hand_landmarks.landmark[tips_ids[0]].x < hand_landmarks.landmark[tips_ids[0]-1].x:
                fingers.append(1)
            else:
                fingers.append(0)
            for id in range(1, 5):
                if hand_landmarks.landmark[tips_ids[id]].y < hand_landmarks.landmark[tips_ids[id]-2].y:
                    fingers.append(1)
                else:
                    fingers.append(0)
            
            # Detectar el signo (letra) usando la función para LSC
            sign = detect_sign_lsc(fingers, hand_landmarks)
            if sign != "":
                current_sign = sign
            
            # Mostrar el signo detectado cerca de la mano
            cv2.putText(frame, current_sign, 
                        (int(hand_landmarks.landmark[0].x * width),
                         int(hand_landmarks.landmark[0].y * height) - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Dibujar un rectángulo negro en la parte inferior para el fondo del texto
    text_position = (10, height - 20)
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 1
    thickness = 2
    (text_width, text_height), _ = cv2.getTextSize(sentence, font, scale, thickness)
    cv2.rectangle(frame, (text_position[0] - 10, text_position[1] - text_height - 10),
                  (text_position[0] + text_width + 10, text_position[1] + 10), (0, 0, 0), -1)
    
    # Escribir la oración en color blanco sobre el rectángulo
    cv2.putText(frame, sentence, text_position, font, scale, (255, 255, 255), thickness)
    
    key = cv2.waitKey(5) & 0xFF
    # Al presionar 'q', se agrega el signo actual a la oración (ahora se permite duplicados consecutivos)
    if key == ord('q'):
        if current_sign != "":
            sentence += current_sign
    # Al presionar la barra espaciadora se añade un espacio a la oración
    elif key == 32:
        sentence += " "
    # Al presionar 'x' se borra el texto actual
    elif key == ord('x'):
        sentence = ""
    
    if key == 27:  # Presionar 'Esc' para salir
        break

    cv2.imshow("Traductor de Lenguaje de Senas - LSC", frame)

# Liberar recursos
hands.close()
cap.release()
cv2.destroyAllWindows()
