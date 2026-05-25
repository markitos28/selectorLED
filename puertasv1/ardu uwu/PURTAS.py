import cv2
import mediapipe as mp
import serial
import time
import math

# ---------------------------
# Intentar conectar al Arduino
# ---------------------------
arduino = None
arduino_conectado = False

try:
    arduino = serial.Serial('COM6', 9600, timeout=1)  # cambia COM si es necesario
    time.sleep(2)
    arduino_conectado = True
except Exception as e:
    print("⚠ No se pudo conectar con Arduino:", e)
    arduino = None
    arduino_conectado = False

# ---------------------------
# Inicializar mediapipe
# ---------------------------
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

cap = cv2.VideoCapture(0)

def contar_dedos(hand_landmarks, mano):
    dedos = 0
    # detectar pulgar (según la mano)
    if mano == "Right":
        if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
            dedos += 1
    else:  # Left
        if hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x:
            dedos += 1

    # otros dedos
    for tip in [8, 12, 16, 20]:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            dedos += 1
    return dedos

def calcular_brillo(hand_landmarks, width, height):
    # Coordenadas en pixeles
    ix, iy = int(hand_landmarks.landmark[8].x * width), int(hand_landmarks.landmark[8].y * height)
    px, py = int(hand_landmarks.landmark[4].x * width), int(hand_landmarks.landmark[4].y * height)

    # Distancia Euclidiana
    distancia = math.hypot(ix - px, iy - py)

    # Escalar la distancia a un rango 0–255
    distancia_min = 20   # dedos casi juntos
    distancia_max = 200  # dedos muy separados
    distancia = max(min(distancia, distancia_max), distancia_min)
    brillo = int(((distancia - distancia_min) / (distancia_max - distancia_min)) * 255)

    return brillo, (ix, iy), (px, py)

# ---------------------------
# Variables de estado
# ---------------------------
led_actual = 0
brillo_actual = 0
ultimo_led = -1
ultimo_brillo = -1

# ---------------------------
# Bucle principal
# ---------------------------
with mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7) as hands:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        h, w, _ = frame.shape

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Reset por defecto
        led_tmp = 0
        brillo_tmp = 0

        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, hand_label in zip(results.multi_hand_landmarks,
                                                 results.multi_handedness):
                mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

                mano = hand_label.classification[0].label  # "Left" o "Right"

                if mano == "Right":
                    dedos = contar_dedos(hand_landmarks, mano)
                    if dedos == 1:
                        led_tmp = 1001   # Servo1
                    elif dedos == 2:
                        led_tmp = 1002   # Servo2
                    elif dedos >= 3 and dedos <= 5:
                        led_tmp = dedos  # LEDs 3,4,5
                    else:
                        led_tmp = 0

                    cv2.putText(image,
                                f"Comando -> {led_tmp}",
                                (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1.2, (0, 255, 0), 3)

                elif mano == "Left":
                    brillo_tmp, indice, pulgar = calcular_brillo(hand_landmarks, w, h)

                    # Dibujar línea entre índice y pulgar
                    cv2.line(image, indice, pulgar, (255, 0, 0), 3)
                    cv2.circle(image, indice, 8, (0, 255, 0), -1)
                    cv2.circle(image, pulgar, 8, (0, 255, 0), -1)

                    cv2.putText(image,
                                f"Brillo -> {brillo_tmp}",
                                (50, 150),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1.2, (255, 0, 0), 3)

        # Actualizar valores globales
        led_actual, brillo_actual = led_tmp, brillo_tmp

        # Enviar al Arduino solo si hay cambios
        if arduino_conectado and (led_actual != ultimo_led or brillo_actual != ultimo_brillo):
            try:
                data = f"{led_actual},{brillo_actual}\n"
                arduino.write(data.encode())
                ultimo_led, ultimo_brillo = led_actual, brillo_actual
            except Exception as e:
                print("⚠ Error enviando datos a Arduino:", e)
                arduino_conectado = False

        # Estado conexión
        if arduino_conectado:
            cv2.putText(image, "Arduino: Conectado", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
        else:
            cv2.putText(image, "Arduino: Desconectado", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

        cv2.imshow("Control bimanual", image)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break

cap.release()
cv2.destroyAllWindows()

if arduino is not None:
    arduino.close()