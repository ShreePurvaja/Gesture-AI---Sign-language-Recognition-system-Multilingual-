import cv2
import mediapipe as mp
import numpy as np
import joblib
import math
from PIL import ImageFont, ImageDraw, Image
from languages import LANG_MAP

model = joblib.load("xgb_sign_model.pkl")
labels = np.load("labels.npy", allow_pickle=True).item()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
draw = mp.solutions.drawing_utils

# Load Unicode font (important for Tamil/Hindi)
font_en = ImageFont.truetype("NotoSans-Regular.ttf", 48)
font_ta = ImageFont.truetype("NotoSansTamil-Regular.ttf", 48)
font_hi = ImageFont.truetype("NotoSansDevanagari-Regular.ttf", 48)


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

    pts = [(x - wrist[0], y - wrist[1]) for x, y in pts]
    scale = np.linalg.norm(np.array(pts[12]))
    pts = [(x/scale, y/scale) for x, y in pts]

    features = []

    fingers = [
        [0,5,8], [0,9,12], [0,13,16],
        [0,17,20], [0,2,4]
    ]
    for a,b,c in fingers:
        features.append(angle(pts[a], pts[b], pts[c]))

    tips = [4,8,12,16,20]
    for i in range(len(tips)):
        for j in range(i+1, len(tips)):
            features.append(distance(pts[tips[i]], pts[tips[j]]))

    return features

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        row = []

        for hand in result.multi_hand_landmarks:
            row.extend(extract_hand_features(hand))
            draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

        if len(result.multi_hand_landmarks) == 1:
            row.extend([0]*15)

        pred = model.predict([row])[0]
        word_en = labels[pred]

        # Get Tamil & Hindi
        word_ta = LANG_MAP[word_en]["ta"]
        word_hi = LANG_MAP[word_en]["hi"]

        # Convert frame to PIL to draw Unicode text
        img_pil = Image.fromarray(frame)
        draw_pil = ImageDraw.Draw(img_pil)

        draw_pil.text((40, 30),  f"English : {word_en}", font=font_en, fill=(0,255,0))
        draw_pil.text((40, 90),  f"Tamil   : {word_ta}", font=font_ta, fill=(0,255,0))
        draw_pil.text((40, 150), f"Hindi   : {word_hi}", font=font_hi, fill=(0,255,0))


        frame = np.array(img_pil)

    cv2.imshow("Sign XGBoost", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
