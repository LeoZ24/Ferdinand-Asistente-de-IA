import cv2
import mediapipe as mp
import serial
import time
import sys

# Configuración de la conexión con micro:bit
try:
    microbit_port = '/dev/tty.usbmodem11402'
    microbit = serial.Serial(microbit_port, 115200, timeout=1)
    print(f"Conexión con micro:bit en {microbit_port} exitosa.")
    time.sleep(2)  # Esperar a que la conexión se establezca
except serial.SerialException:
    print(f"Error: No se pudo conectar con la micro:bit en el puerto {microbit_port}.")
    print("El programa continuará sin enviar comandos al robot.")
    microbit = None

# Inicialización de MediaPipe para detección de manos
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.3
)

# Inicializar la cámara
cap = cv2.VideoCapture(0)

# Obtener dimensiones de la cámara
ret, frame = cap.read()
if not ret:
    print("Error al acceder a la cámara")
    sys.exit(1)

frame_height, frame_width = frame.shape[:2]

# Definir el rectángulo central (30% del tamaño de la imagen)
rect_width = int(frame_width * 0.3)
rect_height = int(frame_height * 0.3)
rect_x = (frame_width - rect_width) // 2
rect_y = (frame_height - rect_height) // 2
rect_center = (rect_x + rect_width // 2, rect_y + rect_height // 2)

# Variables para control de envío de comandos
last_command = None
command_cooldown = 0.1  # Tiempo mínimo entre comandos
last_command_time = 0

def enviar_comando(comando):
    global last_command, last_command_time
    current_time = time.time()
    
    # Verificar si ha pasado suficiente tiempo desde el último comando (0.45 segundos)
    if current_time - last_command_time < 0.45:
        return
    
    # Solo enviar si el comando es diferente al anterior
    if comando != last_command:
        if microbit:
            try:
                # Esperar un momento antes de enviar el siguiente comando
                time.sleep(0.1)
                # Enviar el comando una sola vez cuando cambia
                microbit.write(f"{comando}\n".encode('utf-8'))
                print(f"Comando enviado: {comando}")
                last_command = comando
                last_command_time = current_time
            except Exception as e:
                print(f"Error enviando comando: {e}")
        else:
            last_command = comando # Actualizar último comando incluso sin micro:bit

def determinar_posicion(dedo_x, dedo_y):
    # Margen para la zona "centrado" (10% del tamaño del rectángulo)
    margen_x = rect_width * 0.1
    margen_y = rect_height * 0.1
    
    # Verificar si el dedo está dentro del área "centrado"
    if (abs(dedo_x - rect_center[0]) < margen_x and 
        abs(dedo_y - rect_center[1]) < margen_y):
        return "centrado"
        
    # Verificar posición relativa al rectángulo
    if dedo_x < rect_x:
        return "izquierda"
    elif dedo_x > rect_x + rect_width:
        return "derecha"
    elif dedo_y < rect_y:
        return "arriba"
    elif dedo_y > rect_y + rect_height:
        return "abajo"
    
    return "centrado"

print("Iniciando detección... Presiona 'q' para salir.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        continue

    # Voltear el frame horizontalmente para una visualización más intuitiva
    frame = cv2.flip(frame, 1)
    
    # Convertir a RGB para MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    # Dibujar el rectángulo central
    cv2.rectangle(frame, 
                 (rect_x, rect_y), 
                 (rect_x + rect_width, rect_y + rect_height), 
                 (0, 255, 0), 2)
    
    # Dibujar punto central
    cv2.circle(frame, rect_center, 5, (0, 0, 255), -1)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Dibujar landmarks de la mano
            mp_drawing.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Obtener la posición del dedo índice (landmark 8)
            indice_x = int(hand_landmarks.landmark[8].x * frame_width)
            indice_y = int(hand_landmarks.landmark[8].y * frame_height)
            
            # Dibujar círculo en la punta del dedo índice
            cv2.circle(frame, (indice_x, indice_y), 8, (255, 0, 0), -1)
            
            # Determinar y enviar comando basado en la posición
            posicion = determinar_posicion(indice_x, indice_y)
            enviar_comando(posicion)
            
            # Mostrar comando actual en la pantalla
            cv2.putText(frame, f"Comando: {posicion}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                       1, (255, 255, 255), 2)
    else:
        # Si no se detecta ninguna mano, enviar comando "centrado"
        enviar_comando("centrado")
        # Mostrar comando actual en la pantalla
        cv2.putText(frame, "Comando: centrado", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                   1, (255, 255, 255), 2)

    # Mostrar el frame
    cv2.imshow('Control de Cuello', frame)

    # Salir con 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar recursos
print("Cerrando programa...")
hands.close()
cap.release()
cv2.destroyAllWindows()
if microbit:
    microbit.close()
    print("Conexión con micro:bit cerrada.")
