import cv2
import mediapipe as mp
import serial
import time
import math

# ---------------------------
# Conexión con Arduino
# ---------------------------
arduino = None
arduino_conectado = False

try:
    arduino = serial.Serial('COM5', 9600, timeout=1)
    time.sleep(2)
    arduino_conectado = True
except Exception as e:
    print("⚠ No se pudo conectar con Arduino:", e)

# ---------------------------
# Inicializar mediapipe
# ---------------------------
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

cap = cv2.VideoCapture(0)

def contar_dedos(hand_landmarks, mano):
    dedos = [0, 0, 0, 0, 0]  # pulgar → meñique

    # Pulgar
    if mano == "Right":
        dedos[0] = int(hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x)
    else:
        dedos[0] = int(hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x)

    # Otros dedos
    tips = [8, 12, 16, 20]
    for i, tip in enumerate(tips, start=1):
        dedos[i] = int(hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y)

    return dedos  # lista de 5 (1 o 0)

def calcular_brillo(hand_landmarks, width, height):
    ix, iy = int(hand_landmarks.landmark[8].x * width), int(hand_landmarks.landmark[8].y * height)
    px, py = int(hand_landmarks.landmark[4].x * width), int(hand_landmarks.landmark[4].y * height)
    distancia = math.hypot(ix - px, iy - py)

    distancia_min, distancia_max = 20, 200
    distancia = max(min(distancia, distancia_max), distancia_min)
    brillo = int(((distancia - distancia_min) / (distancia_max - distancia_min)) * 255)

    return brillo, (ix, iy), (px, py)

# ---------------------------
# Variables
# ---------------------------
ultimo_estado = ""
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

        dedos_right = [0, 0, 0, 0, 0]
        brillo_tmp = 0

        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, hand_label in zip(results.multi_hand_landmarks, results.multi_handedness):
                mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                mano = hand_label.classification[0].label

                if mano == "Right":
                    dedos_right = contar_dedos(hand_landmarks, mano)
                    cv2.putText(image, f"Dedos -> {sum(dedos_right)}", (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

                elif mano == "Left":
                    brillo_tmp, indice, pulgar = calcular_brillo(hand_landmarks, w, h)
                    cv2.line(image, indice, pulgar, (255, 0, 0), 3)
                    cv2.circle(image, indice, 8, (0, 255, 0), -1)
                    cv2.circle(image, pulgar, 8, (0, 255, 0), -1)
                    cv2.putText(image, f"Brillo -> {brillo_tmp}", (50, 150),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 0, 0), 3)

        # Crear cadena con el estado de los 5 dedos
        estado = "".join(str(d) for d in dedos_right)

        # Enviar si hay cambios
        if arduino_conectado and (estado != ultimo_estado or brillo_tmp != ultimo_brillo):
            try:
                data = f"{estado},{brillo_tmp}\n"
                arduino.write(data.encode())
                ultimo_estado = estado
                ultimo_brillo = brillo_tmp
            except Exception as e:
                print("⚠ Error enviando datos a Arduino:", e)
                arduino_conectado = False

        color = (0, 255, 0) if arduino_conectado else (0, 0, 255)
        estado_txt = "Conectado" if arduino_conectado else "Desconectado"
        cv2.putText(image, f"Arduino: {estado_txt}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)

        cv2.imshow("Control bimanual", image)
        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
if arduino:
    arduino.close()