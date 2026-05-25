import cv2
import mediapipe as mp
import pyautogui
import math


mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

screen_width, screen_height = pyautogui.size()

dragging = False  

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            landmarks = hand_landmarks.landmark

        
            index_finger = landmarks[8]
            x = int(index_finger.x * frame.shape[1])
            y = int(index_finger.y * frame.shape[0])

            screen_x = int(index_finger.x * screen_width)
            screen_y = int(index_finger.y * screen_height)

            
            pyautogui.moveTo(screen_x, screen_y, duration=0)

            
            thumb = landmarks[4]
            thumb_x, thumb_y = int(thumb.x * frame.shape[1]), int(thumb.y * frame.shape[0])

            distance = math.hypot(x - thumb_x, y - thumb_y)

            
            if distance < 40:
                if not dragging:
                    pyautogui.mouseDown()  
                    dragging = True
            else:
                if dragging:
                    pyautogui.mouseUp()  
                    dragging = False

            
            cv2.circle(frame, (x, y), 10, (0, 255, 0), -1)
            cv2.putText(frame, f"Distancia: {int(distance)}", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Air Mouse con la mano", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

