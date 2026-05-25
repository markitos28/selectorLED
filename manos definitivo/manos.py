"""
hand_leds_servos.py
- Requiere: mediapipe, opencv-python, pyserial
- Cambiar SERIAL_PORT por el puerto correcto (ej. 'COM5' o '/dev/ttyUSB0')
"""

import cv2
import mediapipe as mp
import math
import serial
import time

# ---------- CONFIG ----------
SERIAL_PORT = 'COM6'   # <-- Cambia esto al puerto correcto
BAUDRATE = 9600

# Parámetros de mapeo
LED_MIN = 0
LED_MAX = 255

# Modo inicial
MODE_LED = "LED"
MODE_SERVO = "SERVO"

# Pines / cantidades lógicas (no necesarios para Python, pero para mostrar)
NUM_LEDS = 5
NUM_SERVOS = 2

# ---------- Iniciar Serial ----------
try:
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    time.sleep(2)
    print(f"Serial conectado en {SERIAL_PORT}")
except Exception as e:
    ser = None
    print("No se pudo conectar por serial. Ejecutando en modo simulación. Cambia SERIAL_PORT si quieres comunicación real.")
    print("Error:", e)

def send_serial(cmd):
    """Envía linea por serial (terminada en newline) si serial está disponible."""
    if ser:
        try:
            ser.write((cmd + '\n').encode())
        except Exception as e:
            print("Error enviando serial:", e)
    else:
        # modo simulación / debug
        print("[SIM SERIAL] ->", cmd)

# ---------- Mediapipe setup ----------
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

# ---------- Helpers ----------
def distance_point(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def fingers_up(hand_landmarks, hand_label):
    """
    Devuelve una lista booleana [thumb, index, middle, ring, pinky]
    True si el dedo está levantado (simple heurística).
    hand_label: 'Left' o 'Right' (para la lógica del pulgar)
    """
    lm = hand_landmarks.landmark
    tips_ids = [4, 8, 12, 16, 20]
    pip_ids = [3, 6, 10, 14, 18]  # aproximado, para comparar

    res = [False]*5

    # Para los 4 dedos (index..pinky): comparar y del tip con y del pip
    for i in range(1,5):
        tip = lm[tips_ids[i]]
        pip = lm[pip_ids[i]]
        # si el tip y está por encima (y menor en coordenada) al pip -> levantado
        if tip.y < pip.y:
            res[i] = True
        else:
            res[i] = False

    # Pulgar: comparar en x según mano
    thumb_tip = lm[4]
    thumb_ip  = lm[3]
    if hand_label == 'Right':
        # para mano derecha, pulgar hacia la izquierda (tip.x < ip.x) cuando está abierto (esto depende de orientación)
        res[0] = thumb_tip.x < thumb_ip.x
    else:
        # mano izquierda
        res[0] = thumb_tip.x > thumb_ip.x

    return res

def count_fingers_bool(bool_list):
    return sum(1 for b in bool_list if b)

def is_rock_gesture(bool_list):
    # gesto tipo 🤟: pulgar, indice, meñique arriba; medio y anular abajo
    # indices: [thumb, index, middle, ring, pinky]
    return bool_list[0] and bool_list[1] and (not bool_list[2]) and (not bool_list[3]) and bool_list[4]

# ---------- Estado ----------
current_mode = MODE_LED
prev_mode = current_mode

selected_number = 0 # número seleccionado (1..5 en LED mode, 1..2 en servo mode). 0 = ninguno/mano cerrada
prev_selected = 0

# Para evitar enviar el mismo comando muchas veces
last_led_cmd = None
last_servo_cmds = {1: None, 2: None}

# ---------- Video capture ----------
cap = cv2.VideoCapture(0)

with hands:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)  # espejo para que sea intuitivo
        h, w, _ = frame.shape

        # convertir a RGB
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(img_rgb)

        # por defecto: no hay manos detectadas
        left_hand_landmarks = None
        right_hand_landmarks = None
        left_label = None
        right_label = None

        if result.multi_hand_landmarks and result.multi_handedness:
            # multiparallel: asociar landmarks con handedness
            for idx, hand_handedness in enumerate(result.multi_handedness):
                label = hand_handedness.classification[0].label  # 'Left' o 'Right'
                lm = result.multi_hand_landmarks[idx]
                if label == 'Left':
                    left_hand_landmarks = lm
                    left_label = label
                else:
                    right_hand_landmarks = lm
                    right_label = label

        # dibujar manos detectadas
        if result.multi_hand_landmarks:
            for lm in result.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)

        # Procesar mano izquierda (selector)
        left_count = 0
        if left_hand_landmarks:
            bools = fingers_up(left_hand_landmarks, 'Left')
            left_count = count_fingers_bool(bools)  # 0..5
            # si left_count == 0 -> apagar todos leds
            if current_mode == MODE_LED:
                if left_count == 0:
                    # apagar todos los leds
                    cmd = f"l0:0"
                    if cmd != last_led_cmd:
                        send_serial(cmd)
                        last_led_cmd = cmd
                    selected_number = 0
                else:
                    # seleccionar LED n = left_count (1..5)
                    selected_number = left_count
                    # (no envio aún intensidad, eso lo hará la mano derecha)
            else:
                # modo servo
                if left_count == 1:
                    selected_number = 1
                elif left_count == 2:
                    selected_number = 2
                elif left_count == 0:
                    selected_number = 0
                else:
                    # more than 2 fingers -> ignorar (según tu pedido)
                    # dejamos selected_number sin cambios o 0. Mejor: 0 para evitar activaciones inesperadas.
                    selected_number = 0
        else:
            left_count = 0
            # si no detecta mano izquierda, no forzamos apagado; mantenemos estado anterior
            # podrías decidir apagar -> aquí no hacemos nada

        # Procesar mano derecha (modificador)
        if right_hand_landmarks:
            bools_r = fingers_up(right_hand_landmarks, 'Right')
            # detectar gesto 🤟 para alternar modo (solo cuando se detecta la acción)
            if is_rock_gesture(bools_r):
                # Cambiar modo solo cuando detectamos por primera vez (evitar togglear en cada frame)
                if prev_mode != 'rock_pressed':
                    # alternar
                    current_mode = MODE_SERVO if current_mode == MODE_LED else MODE_LED
                    print("Modo cambiado a:", current_mode)
                    prev_mode = 'rock_pressed'
                # marcar que gesto está presionado (para evitar toggle continuo)
            else:
                # liberar el estado del gesto
                if prev_mode == 'rock_pressed':
                    prev_mode = None

            # dibujar línea entre pulgar (4) e indice (8)
            lm = right_hand_landmarks.landmark
            thumb = (int(lm[4].x * w), int(lm[4].y * h))
            index = (int(lm[8].x * w), int(lm[8].y * h))
            cv2.line(frame, thumb, index, (0, 255, 0), 2)
            # calcular distancia normalizada
            raw_dist = distance_point(thumb, index)
            # normalización por la distancia entre muñeca (0) y medio_mcp (9) para escala relativa
            wrist = (int(lm[0].x * w), int(lm[0].y * h))
            mid_mcp = (int(lm[9].x * w), int(lm[9].y * h))
            norm_factor = max(1.0, distance_point(wrist, mid_mcp))
            norm = raw_dist / norm_factor

            # Mapear norm a 0..255
            # experimenta con estos factores si quieres otra sensibilidad
            # supongamos que norm 0.2 -> 0 , norm 1.0 -> 255
            mapped = int((norm - 0.15) / (1.0 - 0.15) * (LED_MAX - LED_MIN) + LED_MIN)
            mapped = max(LED_MIN, min(LED_MAX, mapped))

            # Si estamos en modo LED y hay un LED seleccionado, enviar intensidad
            if current_mode == MODE_LED and selected_number >= 1 and selected_number <= NUM_LEDS:
                cmd = f"l{selected_number}:{mapped}"
                if cmd != last_led_cmd:
                    send_serial(cmd)
                    last_led_cmd = cmd
            # En modo servo no usamos la distancia segun tu especificacion (los servos actuan binario al seleccionar)
        else:
            # si no hay mano derecha: no dibujar linea ni cambiar intensidad, no enviamos nada
            pass

        # --- Gestión de servos: abrir 90 cuando seleccionado, volver a 0 cuando ya no ---
        if current_mode == MODE_SERVO:
            # si selected_number == 1 -> servo1 a 90; si 2 -> servo2 a 90; si 0 -> ninguno
            # Envia comando s1:90 o s1:0 según cambio
            for s in [1, 2]:
                if selected_number == s:
                    cmd = f"s{s}:90"
                else:
                    cmd = f"s{s}:0"
                if last_servo_cmds[s] != cmd:
                    send_serial(cmd)
                    last_servo_cmds[s] = cmd
            # evitar que leds sigan con valores viejos
            last_led_cmd = None
        else:
            # Si volvemos a modo LED, asegurarnos que servos estén a 0 si no se necesitan
            for s in [1,2]:
                cmd = f"s{s}:0"
                if last_servo_cmds[s] != cmd:
                    send_serial(cmd)
                    last_servo_cmds[s] = cmd

        # --- Interface en pantalla ---
        # Texto: DEDOS: <left_count>
        cv2.rectangle(frame, (5,5), (260,100), (0,0,0), -1)  # fondo opaco para legibilidad
        cv2.putText(frame, f"DEDOS: {left_count}", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
        cv2.putText(frame, f"MODO: {current_mode}", (10,60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
        cv2.putText(frame, f"SELECCION: {selected_number}", (10,88), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

        # mostrar ventana
        cv2.imshow("Control LEDs/Servos - manos", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC para salir
            break

cap.release()
cv2.destroyAllWindows()
if ser:
    ser.close()
