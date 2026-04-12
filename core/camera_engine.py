import cv2
import threading
import time

class CameraEngine:
    def __init__(self):
        self.current_frame = None
        self.is_running = False
        # We call the new robust initializer here
        self.cap = self._initialize_hardware()

    def _initialize_hardware(self):
        """Robustly tests indices 1 and 0 with a warm-up retry loop."""
        print("[System] Searching for valid camera...")
        
        for index in [1, 0]:
            print(f"[System] Testing index {index}...")
            cap = cv2.VideoCapture(index)
            
            if cap.isOpened():
                # Warm-up loop: Try to read a frame 10 times (1 second total)
                # This is critical for Continuity Camera on macOS
                for attempt in range(10):
                    ret, _ = cap.read()
                    if ret:
                        print(f"[System] Camera locked onto index {index}")
                        return cap
                    time.sleep(0.1)
            
            cap.release()
            
        print("[Error] No working cameras found.")
        return None

    def start(self):
        if self.cap:
            self.is_running = True
            threading.Thread(target=self._worker, daemon=True).start()

    def stop(self):
        self.is_running = False
        time.sleep(0.5)
        if self.cap:
            self.cap.release()

    def _worker(self):
        while self.is_running:
            if self.cap is not None:
                # We do a 'grab' to quickly skip any old frames in the buffer
                # then a 'retrieve' to get the fresh one. 
                self.cap.grab() 
                success, frame = self.cap.retrieve()
                
                if success:
                    # Flip the frame for the mirror effect
                    self.current_frame = cv2.flip(frame, 1)
                else:
                    time.sleep(0.01)
            else:
                time.sleep(0.1)