import os
import cv2
import mediapipe as mp
import numpy as np

DATASET = "dataset"

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=True)

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
                row.extend(get_vector(hand))

            if len(result.multi_hand_landmarks) == 1:
                row.extend([0]*42)

            X.append(row)
            y.append(label_id)

    print(word, "done")
    label_id += 1

np.save("X.npy", np.array(X))
np.save("y.npy", np.array(y))
np.save("labels.npy", labels)

print("Saved", len(X), "samples")
