import cv2
import mediapipe as mp
import numpy as np
import joblib

model = joblib.load("rf_model.pkl")
labels = np.load("labels.npy", allow_pickle=True).item()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
draw = mp.solutions.drawing_utils

def get_vector(hand):
    wrist = hand.landmark[0]
    pts = []

    for lm in hand.landmark:
        x = lm.x - wrist.x
        y = lm.y - wrist.y
        pts.append([x, y])

    pts = np.array(pts)
    scale = np.linalg.norm(pts[12])
    pts = pts / scale

    return pts.flatten().tolist()

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        row = []

        for hand in result.multi_hand_landmarks:
            row.extend(get_vector(hand))
            draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

        if len(result.multi_hand_landmarks) == 1:
            row.extend([0]*42)

        pred = model.predict([row])[0]
        word = labels[pred]

        cv2.putText(frame, word, (50,80),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0,255,0), 4)

    cv2.imshow("Sign RF", frame)
    if cv2.waitKey(1) == 27:
        break
