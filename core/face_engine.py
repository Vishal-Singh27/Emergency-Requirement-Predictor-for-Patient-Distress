import cv2
import threading
import time
import collections
from deepface import DeepFace

class FaceAnalyzer:
    def __init__(self, scale_factor=4):
        self.scale_factor = scale_factor
        self.current_score = 0
        self.current_box = (0, 0, 0, 0)
        self.is_running = False
        self.engine_active = False
        
        self.score_history = collections.deque(maxlen=5)
        self.box_history = collections.deque(maxlen=5)

    def start(self, camera_engine):
        self.is_running = True
        threading.Thread(target=self._worker, args=(camera_engine,), daemon=True).start()

    def stop(self):
        self.is_running = False

    def _worker(self, camera_engine):
        while self.is_running:
            if self.engine_active and camera_engine.current_frame is not None:
                frame_to_analyze = camera_engine.current_frame.copy()
                small_frame = cv2.resize(frame_to_analyze, (0, 0), fx=1/self.scale_factor, fy=1/self.scale_factor)
                try:
                    results = DeepFace.analyze(small_frame, actions=['emotion'], enforce_detection=False, detector_backend='opencv', silent=True)
                    emotions = results[0]['emotion']
                    
                    # Tamed emotion weighting
                    raw_score = emotions['fear'] + emotions['sad'] + (emotions['angry'] * 0.2) + (emotions['disgust'] * 0.2)
                    raw_score = min(100.0, raw_score)
                    
                    raw_box = (
                        int(results[0]['region']['x'] * self.scale_factor), 
                        int(results[0]['region']['y'] * self.scale_factor), 
                        int(results[0]['region']['w'] * self.scale_factor), 
                        int(results[0]['region']['h'] * self.scale_factor)
                    )
                    
                    self.score_history.append(raw_score)
                    self.box_history.append(raw_box)
                    
                    self.current_score = sum(self.score_history) / len(self.score_history)
                    self.current_box = (
                        int(sum(b[0] for b in self.box_history) / len(self.box_history)),
                        int(sum(b[1] for b in self.box_history) / len(self.box_history)),
                        int(sum(b[2] for b in self.box_history) / len(self.box_history)),
                        int(sum(b[3] for b in self.box_history) / len(self.box_history))
                    )
                except Exception:
                    pass
                time.sleep(0.05)
            else:
                self.current_score = 0
                self.current_box = (0, 0, 0, 0)
                time.sleep(0.1)