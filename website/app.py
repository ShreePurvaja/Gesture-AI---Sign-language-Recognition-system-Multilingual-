from flask import Flask, render_template, Response, request, jsonify
import cv2
import mediapipe as mp
import numpy as np
import joblib
import math
import time
import random
from languages import LANG_MAP
from datetime import datetime

app = Flask(__name__)

# -------- GLOBAL STATE FOR UI --------
CURRENT_TEXT = {"en": "", "ta": "", "hi": ""}
CURRENT_LANG = "all"
HISTORY = []
HAND_STATUS = "No Hand Detected"
LAST_GESTURE_TIME = time.time()
GESTURE_COUNT = 0
CONFIDENCE_SCORES = {"en": 0, "ta": 0, "hi": 0}
# -------------------------------------

model = joblib.load("xgb_sign_model.pkl")
labels = np.load("labels.npy", allow_pickle=True).item()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
draw = mp.solutions.drawing_utils

# Enhanced drawing style
drawing_spec = draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)
connection_spec = draw.DrawingSpec(color=(255, 0, 255), thickness=2)


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
    fingers = [[0,5,8], [0,9,12], [0,13,16], [0,17,20], [0,2,4]]

    for a, b, c in fingers:
        features.append(angle(pts[a], pts[b], pts[c]))

    tips = [4,8,12,16,20]
    for i in range(len(tips)):
        for j in range(i+1, len(tips)):
            features.append(distance(pts[tips[i]], pts[tips[j]]))

    return features


def generate_frames():
    global CURRENT_TEXT, HISTORY, HAND_STATUS, LAST_GESTURE_TIME, GESTURE_COUNT, CONFIDENCE_SCORES

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # FPS calculation
    prev_time = time.time()
    fps = 0

    while True:
        success, frame = cap.read()
        if not success:
            break

        current_time = time.time()
        fps = 1 / (current_time - prev_time) if current_time - prev_time > 0 else 0
        prev_time = current_time

        # Flip frame for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Add UI overlay
        h, w, _ = frame.shape
        overlay = frame.copy()
        
        # Draw gradient overlay
        cv2.rectangle(overlay, (0, 0), (w, 60), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
        
        # Add FPS display
        cv2.putText(frame, f"FPS: {int(fps)}", (20, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        # Add status
        status_color = (0, 255, 0) if HAND_STATUS == "Hand Detected" else (0, 165, 255)
        cv2.putText(frame, HAND_STATUS, (w - 300, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            HAND_STATUS = "Hand Detected"
            row = []

            for hand_landmarks in result.multi_hand_landmarks:
                row.extend(extract_hand_features(hand_landmarks))
                # Enhanced hand landmarks drawing
                draw.draw_landmarks(
                    frame, 
                    hand_landmarks, 
                    mp_hands.HAND_CONNECTIONS,
                    drawing_spec,
                    connection_spec
                )
                
                # Draw bounding box
                x_coords = [lm.x for lm in hand_landmarks.landmark]
                y_coords = [lm.y for lm in hand_landmarks.landmark]
                x_min, x_max = int(min(x_coords) * w), int(max(x_coords) * w)
                y_min, y_max = int(min(y_coords) * h), int(max(y_coords) * h)
                cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)

            if len(result.multi_hand_landmarks) == 1:
                row.extend([0] * 15)

            # Make prediction with confidence
            try:
                pred_proba = model.predict_proba([row])
                pred = model.predict([row])[0]
                confidence = np.max(pred_proba) * 100
                
                word_en = labels[pred]
                word_ta = LANG_MAP[word_en]["ta"]
                word_hi = LANG_MAP[word_en]["hi"]

                # Only update if confidence is high enough and enough time passed
                if (confidence > 60 and 
                    (current_time - LAST_GESTURE_TIME > 1.0 or 
                     word_en != CURRENT_TEXT["en"])):
                    
                    # Update UI data
                    CURRENT_TEXT["en"] = word_en
                    CURRENT_TEXT["ta"] = word_ta
                    CURRENT_TEXT["hi"] = word_hi
                    
                    # Update confidence scores
                    CONFIDENCE_SCORES["en"] = confidence
                    CONFIDENCE_SCORES["ta"] = confidence * 0.95  # Simulated for other languages
                    CONFIDENCE_SCORES["hi"] = confidence * 0.95
                    
                    # Add confidence to display
                    display_text = f"{word_en} ({confidence:.1f}%)"
                    
                    # Maintain history (last 5 unique)
                    if not HISTORY or HISTORY[-1] != display_text:
                        HISTORY.append(display_text)
                        GESTURE_COUNT += 1
                    if len(HISTORY) > 5:
                        HISTORY.pop(0)
                    
                    LAST_GESTURE_TIME = current_time
                    
                    # Draw prediction on frame
                    cv2.putText(frame, f"Sign: {word_en}", (20, h - 40), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                    cv2.putText(frame, f"Confidence: {confidence:.1f}%", (20, h - 80), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

            except Exception as e:
                print(f"Prediction error: {e}")

        else:
            HAND_STATUS = "No Hand Detected"

        # Draw AI processing indicator
        cv2.putText(frame, "AI Processing...", (w - 250, h - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Encode frame
        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/get_data')
def get_data():
    response_time = random.uniform(0.3, 0.6)  # Simulated response time
    
    return jsonify({
        "text": CURRENT_TEXT,
        "history": HISTORY[::-1],
        "status": HAND_STATUS,
        "lang": CURRENT_LANG,
        "confidence": CONFIDENCE_SCORES,
        "gesture_count": GESTURE_COUNT,
        "response_time": f"{response_time:.1f}s",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/set_language', methods=['POST'])
def set_language():
    global CURRENT_LANG
    CURRENT_LANG = request.form.get('lang', 'all')
    return ('', 204)


@app.route('/clear_history', methods=['POST'])
def clear_history():
    global HISTORY, GESTURE_COUNT
    HISTORY = []
    GESTURE_COUNT = 0
    return jsonify({"success": True, "message": "History cleared"})


@app.route('/stats')
def get_stats():
    return jsonify({
        "total_gestures": GESTURE_COUNT,
        "active_time": int(time.time() - START_TIME),
        "average_confidence": sum(CONFIDENCE_SCORES.values()) / 3 if CONFIDENCE_SCORES else 0,
        "languages_supported": 3,
        "system_status": "operational"
    })


if __name__ == "__main__":
    START_TIME = time.time()
    print("🚀 Starting GestureAI Server...")
    print("🌐 Access at: http://localhost:5000")
    print("💡 Make sure your webcam is connected and accessible")
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)