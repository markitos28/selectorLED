import cv2, mediapipe as mp
import serial, time, math

# ---- Conexión Arduino ----
arduino = serial.Serial('COM6', 9600, timeout=1)  # Cambiar COM según corresponda
time.sleep(2)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

modo = "LED"       # LED o SERVO
ultimo_cambio = 0  # para evitar rebotes
led_actual = 0
brillo_actual = 0
servo_actual = 0
angulo_actual = 90

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

def contar_dedos(hand_landmarks, mano):
    dedos = 0
    if mano == "Right":
        if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
            dedos += 1
    else:
        if hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x:
            dedos += 1
    for tip in [8,12,16,20]:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip-2].y:
            dedos += 1
    return dedos

def calcular_distancia(hand_landmarks, w, h):
    ix, iy = int(hand_landmarks.landmark[8].x * w), int(hand_landmarks.landmark[8].y * h)
    px, py = int(hand_landmarks.landmark[4].x * w), int(hand_landmarks.landmark[4].y * h)
    dist = math.hypot(ix - px, iy - py)
    dist = max(min(dist,200),20)
    return int(((dist-20)/(200-20))*255), (ix,iy), (px,py)

def gesto_cambio(hand_landmarks):
    dedos = []
    for tip in [8,12,16,20]:
        dedos.append(hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip-2].y)
    return dedos[0] and not dedos[1] and not dedos[2] and dedos[3]

with mp_hands.Hands(max_num_hands=2,min_detection_confidence=0.7) as hands:
    while True:
        ret, frame = cap.read()
        if not ret: break
        h,w,_ = frame.shape
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)
        frame = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

        led_tmp = 0
        brillo_tmp = brillo_actual
        servo_tmp = servo_actual
        angulo_tmp = angulo_actual

        if results.multi_hand_landmarks and results.multi_handedness:
            for hand, label in zip(results.multi_hand_landmarks, results.multi_handedness):
                mano = label.classification[0].label
                mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

                # --- Cambio de modo con gesto 🤟 en mano izquierda ---
                if mano == "Left" and gesto_cambio(hand):
                    if time.time() - ultimo_cambio > 1.0:
                        modo = "SERVO" if modo == "LED" else "LED"
                        ultimo_cambio = time.time()

                if modo == "LED":
                    if mano == "Right":
                        dedos = contar_dedos(hand, mano)
                        if dedos > 0: led_tmp = dedos
                    elif mano == "Left":
                        brillo_tmp, i, p = calcular_distancia(hand, w, h)
                        cv2.line(frame, i, p, (255,0,0), 3)
                else: # SERVO
                    if mano == "Right":
                        dedos = contar_dedos(hand, mano)
                        if dedos in [1,2]: servo_tmp = dedos
                    elif mano == "Left":
                        brillo_tmp, i, p = calcular_distancia(hand, w, h)
                        angulo_tmp = int((brillo_tmp/255)*180)
                        cv2.line(frame, i, p, (0,0,255), 3)

        # Envío según modo
        if modo == "LED":
            if (led_tmp != led_actual) or (brillo_tmp != brillo_actual):
                arduino.write(f"LED,{led_tmp},{brillo_tmp}\n".encode())
                led_actual, brillo_actual = led_tmp, brillo_tmp
        else:
            if (servo_tmp != servo_actual) or (angulo_tmp != angulo_actual):
                arduino.write(f"SERVO,{servo_tmp},{angulo_tmp}\n".encode())
                servo_actual, angulo_actual = servo_tmp, angulo_tmp

        cv2.putText(frame, f"Modo: {modo}", (20,40),
                    cv2.FONT_HERSHEY_SIMPLEX,1.2,(0,255,255),3)
        cv2.imshow("Modo LED/SERVO", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
arduino.close()
cv2.destroyAllWindows()