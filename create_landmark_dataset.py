import os
import cv2
import mediapipe as mp
import numpy as np
import math

DATASET = "dataset"

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=True)

def distance(a, b):
    return np.linalg.norm(np.array(a) - np.array(b))

def angle(a, b, c):
    ba = np.array(a) - np.array(b)
    bc = np.array(c) - np.array(b)
    cos = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    return math.degrees(np.arccos(cos))

def extract_hand_features(hand):
    pts = [(lm.x, lm.y) for lm in hand.landmark]
    wrist = pts[0]

    # Normalize
    pts = [(x - wrist[0], y - wrist[1]) for x, y in pts]
    scale = np.linalg.norm(np.array(pts[12]))
    pts = [(x/scale, y/scale) for x, y in pts]

    features = []

    # Finger angles (5)
    fingers = [
        [0,5,8], [0,9,12], [0,13,16],
        [0,17,20], [0,2,4]
    ]
    for a,b,c in fingers:
        features.append(angle(pts[a], pts[b], pts[c]))

    # Fingertip distances (10)
    tips = [4,8,12,16,20]
    for i in range(len(tips)):
        for j in range(i+1, len(tips)):
            features.append(distance(pts[tips[i]], pts[tips[j]]))

    return features

X, y = [], []
labels = {}
label_id = 0

for word in os.listdir(DATASET):
    path = os.path.join(DATASET, word)
    if not os.path.isdir(path):
        continue

    labels[label_id] = word

    for img_name in os.listdir(path):
        img = cv2.imread(os.path.join(path, img_name))
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            row = []

            for hand in result.multi_hand_landmarks:
                row.extend(extract_hand_features(hand))

            if len(result.multi_hand_landmarks) == 1:
                row.extend([0]*15)  # pad second hand

            X.append(row)
            y.append(label_id)

    print(word, "done")
    label_id += 1

np.save("X.npy", np.array(X))
np.save("y.npy", np.array(y))
np.save("labels.npy", labels)

print("Feature dataset created:", len(X))
