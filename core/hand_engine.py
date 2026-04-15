import cv2
import threading
import time
import math
import collections
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class HandAnalyzer:
    def __init__(self):
        self.current_score = 0
        self.current_gesture = "Standby"
        self.current_boxes = []
        self.current_shake_metric = 0  # 0 to 100% intensity
        self.is_running = False
        self.engine_active = False
        
        # --- SHAKING METRICS CONFIG ---
        self.movement_history = collections.deque(maxlen=15) 
        self.MAX_EXPECTED_JITTER = 0.25 # Calibration: Max distance over 15 frames

    def start(self, camera_engine):
        self.is_running = True
        threading.Thread(target=self._worker, args=(camera_engine,), daemon=True).start()

    def stop(self):
        self.is_running = False

    def _worker(self, camera_engine):
        base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
        options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=2)
        detector = vision.HandLandmarker.create_from_options(options)

        while self.is_running:
            if not self.engine_active or camera_engine.current_frame is None:
                self.current_score = 0
                self.current_gesture = "Standby"
                self.current_shake_metric = 0
                self.current_boxes = []
                time.sleep(0.1)
                continue

            try:
                frame_to_analyze = camera_engine.current_frame.copy()
                rgb_frame = cv2.cvtColor(frame_to_analyze, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                detection_result = detector.detect(mp_image)
                
                temp_score = 0
                temp_gesture = "Normal"
                temp_shake_val = 0
                temp_boxes = []

                if detection_result.hand_landmarks:
                    num_hands = len(detection_result.hand_landmarks)
                    wrist = detection_result.hand_landmarks[0][0] 
                    self.movement_history.append((wrist.x, wrist.y))

                    # --- CALCULATE SHAKE METRIC ---
                    if len(self.movement_history) > 10:
                        total_dist = 0
                        for i in range(1, len(self.movement_history)):
                            d = math.sqrt((self.movement_history[i][0] - self.movement_history[i-1][0])**2 + 
                                          (self.movement_history[i][1] - self.movement_history[i-1][1])**2)
                            total_dist += d
                        
                        # Normalize to 0-100%
                        temp_shake_val = min(100, (total_dist / self.MAX_EXPECTED_JITTER) * 100)
                        
                        if temp_shake_val > 40: # Threshold to trigger the label
                            temp_gesture = "HANDS SHAKING"
                            temp_score = int(temp_shake_val * 0.8) # Weight shaking as up to 80% distress

                    for hand_lms in detection_result.hand_landmarks:
                        x_coords = [lm.x for lm in hand_lms]
                        y_coords = [lm.y for lm in hand_lms]
                        temp_boxes.append({'x_min': min(x_coords), 'x_max': max(x_coords), 'y_min': min(y_coords), 'y_max': max(y_coords)})

                    # Check for Choking Overrides (Highest Priority)
                    if num_hands == 1:
                        if 0.3 < wrist.x < 0.7 and 0.5 < wrist.y < 0.95:
                            temp_gesture = "1-HAND CHOKE"
                            temp_score = 100
                    elif num_hands == 2:
                        wrist_2 = detection_result.hand_landmarks[1][0]
                        dist = math.sqrt((wrist.x - wrist_2.x)**2 + (wrist.y - wrist_2.y)**2)
                        if dist < 0.2 and wrist.y < 0.8:
                            temp_gesture = "2-HAND CHOKE"
                            temp_score = 100
                else:
                    self.movement_history.clear()

                self.current_shake_metric = temp_shake_val
                self.current_gesture = temp_gesture
                self.current_score = max(temp_score, self.current_score if temp_score == 0 else temp_score)
                self.current_boxes = temp_boxes
                
            except Exception as e:
                pass

            time.sleep(0.03)