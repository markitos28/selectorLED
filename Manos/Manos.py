import cv2
import mediapipe as mp


mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils


cap = cv2.VideoCapture(1)


finger_tips = [4, 8, 12, 16, 20]

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    if result.multi_hand_landmarks:
        for hand_landmarks, hand_handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            landmarks = hand_landmarks.landmark
            fingers = []

          
            hand_label = hand_handedness.classification[0].label  

            
            if hand_label == "Right":
                if landmarks[finger_tips[0]].x < landmarks[finger_tips[0]-1].x:
                    fingers.append(1)
                else:
                    fingers.append(0)
            else: 
                if landmarks[finger_tips[0]].x > landmarks[finger_tips[0]-1].x:
                    fingers.append(1)
                else:
                    fingers.append(0)

           
            for id in range(1, 5):
                if landmarks[finger_tips[id]].y < landmarks[finger_tips[id]-2].y:
                    fingers.append(1)
                else:
                    fingers.append(0)

            total_fingers = fingers.count(1)

           
            x = int(landmarks[0].x * frame.shape[1])
            y = int(landmarks[0].y * frame.shape[0]) - 20

            cv2.putText(frame, f'Dedos: {total_fingers}', (x, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Detector de dedos - 2 manos", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
