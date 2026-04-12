import cv2
import threading
import time
import math
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class HandAnalyzer:
    def __init__(self):
        self.current_score = 0
        self.current_gesture = "Standby"
        self.current_boxes = []
        self.is_running = False
        self.engine_active = False

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
            if self.engine_active and camera_engine.current_frame is not None:
                frame_to_analyze = camera_engine.current_frame.copy()
                rgb_frame = cv2.cvtColor(frame_to_analyze, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                detection_result = detector.detect(mp_image)
                
                temp_score = 0
                temp_gesture = "Normal"
                temp_boxes = []

                if detection_result.hand_landmarks:
                    num_hands = len(detection_result.hand_landmarks)
                    for hand_lms in detection_result.hand_landmarks:
                        x_coords = [lm.x for lm in hand_lms]
                        y_coords = [lm.y for lm in hand_lms]
                        temp_boxes.append({'x_min': min(x_coords), 'x_max': max(x_coords), 'y_min': min(y_coords), 'y_max': max(y_coords)})

                    # Direct math because the frame is already flipped by CameraEngine
                    if num_hands == 1:
                        wrist = detection_result.hand_landmarks[0][0] 
                        if 0.3 < wrist.x < 0.7 and 0.5 < wrist.y < 0.95:
                            temp_gesture = "1-HAND CHOKE"
                            temp_score = 100
                        else:
                            temp_gesture = "1 Hand Detected"
                            temp_score = 10
                            
                    elif num_hands == 2:
                        wrist_1 = detection_result.hand_landmarks[0][0]
                        wrist_2 = detection_result.hand_landmarks[1][0]
                        distance = math.sqrt((wrist_1.x - wrist_2.x)**2 + (wrist_1.y - wrist_2.y)**2)
                        
                        if distance < 0.2 and wrist_1.y < 0.8 and wrist_2.y < 0.8:
                            temp_gesture = "2-HAND CHOKE"
                            temp_score = 100
                        else:
                            temp_gesture = "2 Hands Detected"
                            temp_score = 20 
                
                self.current_gesture = temp_gesture
                self.current_score = temp_score
                self.current_boxes = temp_boxes
                time.sleep(0.03)
            else:
                self.current_score = 0
                self.current_gesture = "Standby"
                self.current_boxes = []
                time.sleep(0.1)