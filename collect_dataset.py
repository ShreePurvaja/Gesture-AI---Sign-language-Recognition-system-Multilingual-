import cv2
import os
import time

LABEL = "Peace"          # ← change for each word
SAMPLES = 500
SAVE_DIR = f"dataset/{LABEL}"

os.makedirs(SAVE_DIR, exist_ok=True)

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

print("Camera opened. Place your hand inside the box...")
time.sleep(5)   # wait AFTER camera opens

count = 0
start_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    # ✅ Wider collection box
    x1, y1 = int(w*0.25), int(h*0.10)
    x2, y2 = int(w*0.80), int(h*0.90)

    roi = frame[y1:y2, x1:x2]
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 3)

    elapsed = int(time.time() - start_time)

    # Countdown on screen
    if elapsed < 5:
        cv2.putText(frame, f"Starting in {5-elapsed}s",
                    (10,40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    else:
        cv2.imwrite(f"{SAVE_DIR}/{count}.jpg", roi)
        count += 1
        cv2.putText(frame, f"Collecting: {count}/{SAMPLES}",
                    (10,40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    cv2.imshow("Dataset Collector", frame)

    if cv2.waitKey(1) & 0xFF == ord('q') or count >= SAMPLES:
        break

cap.release()
cv2.destroyAllWindows()

print("Images saved for", LABEL)
