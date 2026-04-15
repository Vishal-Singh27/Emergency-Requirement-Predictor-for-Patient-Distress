import tkinter as tk
from tkinter import font
import cv2
from PIL import Image, ImageTk
import sys

# Import our custom modular engines
from core.camera_engine import CameraEngine
from core.face_engine import FaceAnalyzer
from core.hand_engine import HandAnalyzer
from core.vitals_engine import VitalsAnalyzer

class PatientMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Patient Distress Monitor - Modular System")
        self.root.geometry("1280x760")
        self.root.configure(bg="#121212") 
        
        # System State
        self.system_running = False
        
        # Initialize Core Engines
        self.cam = CameraEngine()
        self.face_ai = FaceAnalyzer()
        self.hand_ai = HandAnalyzer()
        self.vitals_ai = VitalsAnalyzer()

        # Safety Check: Did the camera engine find a camera?
        if not self.cam.cap:
            print("Critical Error: Camera hardware not found.")
            sys.exit()

        # Start background hardware threads
        self.cam.start()
        self.face_ai.start(self.cam)
        self.hand_ai.start(self.cam)
        self.vitals_ai.start()
        
        # --- UI LAYOUT ---
        self.main_frame = tk.Frame(root, bg="#121212")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.video_frame = tk.Frame(self.main_frame, bg="#000000", bd=2, relief="flat")
        self.video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.video_label = tk.Label(self.video_frame, bg="black")
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        self.dash_frame = tk.Frame(self.main_frame, bg="#1e1e1e", width=420, bd=0)
        self.dash_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(15, 0))
        self.dash_frame.pack_propagate(False) 
        
        title_font = font.Font(family="Helvetica", size=20, weight="bold")
        self.data_font = font.Font(family="Helvetica", size=16)
        master_font = font.Font(family="Helvetica", size=28, weight="bold")
        btn_font = font.Font(family="Helvetica", size=14, weight="bold")
        
        tk.Label(self.dash_frame, text="Distress Predictor", font=title_font, fg="#ffffff", bg="#1e1e1e").pack(pady=(20, 10))
        
        # --- ENGINE CONTROLS ---
        self.control_frame = tk.Frame(self.dash_frame, bg="#1e1e1e")
        self.control_frame.pack(fill=tk.X, pady=10, padx=20)
        
        self.btn_start = tk.Button(self.control_frame, text="START SYSTEM", font=btn_font, bg="#4CAF50", fg="black", 
                                   highlightbackground="#4CAF50", relief="flat", height=2, command=self.start_system)
        self.btn_start.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.btn_stop = tk.Button(self.control_frame, text="STOP", font=btn_font, bg="#9E9E9E", fg="black", 
                                  highlightbackground="#9E9E9E", relief="flat", height=2, command=self.stop_system)
        self.btn_stop.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

        # --- MODULE TOGGLES (CUSTOM BUTTONS) ---
        self.enable_face = True
        self.enable_hand = True
        self.enable_vitals = True

        self.toggles_frame = tk.Frame(self.dash_frame, bg="#1e1e1e")
        self.toggles_frame.pack(fill=tk.X, pady=5, padx=20)
        
        toggle_font = font.Font(family="Helvetica", size=11, weight="bold")
        
        self.btn_face = tk.Button(self.toggles_frame, text="✓ FACE", font=toggle_font, bg="#4CAF50", fg="black", highlightbackground="#4CAF50", relief="flat", command=lambda: self.toggle_sensor('face'))
        self.btn_face.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        self.btn_hand = tk.Button(self.toggles_frame, text="✓ HANDS", font=toggle_font, bg="#4CAF50", fg="black", highlightbackground="#4CAF50", relief="flat", command=lambda: self.toggle_sensor('hand'))
        self.btn_hand.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 2))

        self.btn_vitals = tk.Button(self.toggles_frame, text="✓ VITALS", font=toggle_font, bg="#4CAF50", fg="black", highlightbackground="#4CAF50", relief="flat", command=lambda: self.toggle_sensor('vitals'))
        self.btn_vitals.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        
        # --- SENSOR DATA LABELS ---
        self.lbl_face = tk.Label(self.dash_frame, text="Face Distress: Standby", font=self.data_font, fg="#aaaaaa", bg="#1e1e1e", justify=tk.LEFT)
        self.lbl_face.pack(pady=12, anchor="w", padx=25)
        
        self.lbl_hand = tk.Label(self.dash_frame, text="Gesture: Standby\nShake Intensity: N/A", font=self.data_font, fg="#aaaaaa", bg="#1e1e1e", justify=tk.LEFT)
        self.lbl_hand.pack(pady=12, anchor="w", padx=25)
        
        self.lbl_vitals = tk.Label(self.dash_frame, text="Heart Rate: Standby", font=self.data_font, fg="#aaaaaa", bg="#1e1e1e", justify=tk.LEFT)
        self.lbl_vitals.pack(pady=12, anchor="w", padx=25)
        
        tk.Frame(self.dash_frame, height=1, bg="#333333").pack(fill=tk.X, pady=30, padx=20)
        
        # --- MASTER SCORE ---
        tk.Label(self.dash_frame, text="SYSTEM STATUS", font=self.data_font, fg="#aaaaaa", bg="#1e1e1e").pack()
        self.lbl_master = tk.Label(self.dash_frame, text="PAUSED", font=master_font, fg="#aaaaaa", bg="#1e1e1e")
        self.lbl_master.pack(pady=10)

        self.btn_exit = tk.Button(self.dash_frame, text="SHUTDOWN SYSTEM", font=btn_font, bg="#E53935", fg="black", 
                                  highlightbackground="#E53935", relief="flat", height=2, command=self.on_closing)
        self.btn_exit.pack(side=tk.BOTTOM, fill=tk.X, pady=20, padx=20) 
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.update_ui_loop()

    def sync_engines(self):
        if self.system_running:
            self.face_ai.engine_active = self.enable_face
            self.hand_ai.engine_active = self.enable_hand
            self.vitals_ai.engine_active = self.enable_vitals
        else:
            self.face_ai.engine_active = False
            self.hand_ai.engine_active = False
            self.vitals_ai.engine_active = False

    def toggle_sensor(self, sensor):
        if sensor == 'face':
            self.enable_face = not self.enable_face
            if self.enable_face:
                self.btn_face.config(text="✓ FACE", bg="#4CAF50", fg="black", highlightbackground="#4CAF50")
            else:
                self.btn_face.config(text="✗ FACE", bg="#9E9E9E", fg="black", highlightbackground="#9E9E9E")
                
        elif sensor == 'hand':
            self.enable_hand = not self.enable_hand
            if self.enable_hand:
                self.btn_hand.config(text="✓ HANDS", bg="#4CAF50", fg="black", highlightbackground="#4CAF50")
            else:
                self.btn_hand.config(text="✗ HANDS", bg="#9E9E9E", fg="black", highlightbackground="#9E9E9E")
                
        elif sensor == 'vitals':
            self.enable_vitals = not self.enable_vitals
            if self.enable_vitals:
                self.btn_vitals.config(text="✓ VITALS", bg="#4CAF50", fg="black", highlightbackground="#4CAF50")
            else:
                self.btn_vitals.config(text="✗ VITALS", bg="#9E9E9E", fg="black", highlightbackground="#9E9E9E")

        self.sync_engines()

    def start_system(self):
        self.system_running = True
        self.sync_engines() 
        self.btn_start.config(bg="#81C784", text="SYSTEM RUNNING")
        self.btn_stop.config(bg="#F44336", text="STOP")

    def stop_system(self):
        self.system_running = False
        self.sync_engines() 
        self.btn_start.config(bg="#4CAF50", text="START SYSTEM")
        self.btn_stop.config(bg="#9E9E9E", text="STOPPED")

    def update_ui_loop(self):
        if self.cam.current_frame is not None:
            frame = self.cam.current_frame.copy()
            img_h, img_w, _ = frame.shape

            if self.system_running:
                if self.face_ai.engine_active:
                    fx, fy, fw, fh = self.face_ai.current_box
                    if fw > 0:
                        cv2.rectangle(frame, (fx, fy), (fx + fw, fy + fh), (255, 255, 255), 1)

                if self.hand_ai.engine_active:
                    for box in self.hand_ai.current_boxes:
                        px_min, px_max = int(box['x_min'] * img_w), int(box['x_max'] * img_w)
                        py_min, py_max = int(box['y_min'] * img_h), int(box['y_max'] * img_h)
                        cv2.rectangle(frame, (px_min, py_min), (px_max, py_max), (255, 255, 0), 1)

                # ==========================================
                # --- NEW DYNAMIC MULTIMODAL FUSION MATH ---
                # ==========================================
                
                # Check exactly what hardware is alive and transmitting
                face_available = self.face_ai.engine_active
                vitals_available = self.vitals_ai.engine_active and self.vitals_ai.is_connected
                hand_available = self.hand_ai.engine_active

                # Pull the raw scores
                face_score = self.face_ai.current_score if face_available else 0
                vitals_score = self.vitals_ai.current_score if vitals_available else 0
                shake_score = self.hand_ai.current_shake_metric if hand_available else 0

                # Initialize weights
                weight_face = 0.0
                weight_vitals = 0.0
                weight_shake = 0.0

                # 3-Way Fusion (All Sensors Active)
                if face_available and vitals_available and hand_available:
                    weight_face, weight_vitals, weight_shake = 0.25, 0.55, 0.20
                
                # 2-Way Fusions (Dynamic Fallbacks)
                elif face_available and vitals_available:
                    weight_face, weight_vitals = 0.3, 0.7
                elif face_available and hand_available:
                    weight_face, weight_shake = 0.6, 0.4
                elif vitals_available and hand_available:
                    weight_vitals, weight_shake = 0.7, 0.3
                
                # 1-Way Fusions (Absolute Fallbacks)
                elif face_available:
                    weight_face = 1.0
                elif vitals_available:
                    weight_vitals = 1.0
                elif hand_available:
                    weight_shake = 1.0

                # Check for Absolute Overrides (Choking or Critical HR)
                override_active = False
                final_distress = 0.0

                if hand_available and self.hand_ai.current_score == 100:
                    final_distress = 100.0
                    override_active = True
                if self.vitals_ai.engine_active and self.vitals_ai.current_score == 100:
                    final_distress = 100.0
                    override_active = True

                # Calculate final score
                if not override_active:
                    final_distress = (face_score * weight_face) + (vitals_score * weight_vitals) + (shake_score * weight_shake)
                
                # ==========================================

                if self.face_ai.engine_active:
                    self.lbl_face.config(text=f"Face Distress: {self.face_ai.current_score:.1f}%", fg="#ff4444" if self.face_ai.current_score > 50 else "#00ff00")
                else:
                    self.lbl_face.config(text="Face Distress: DISABLED", fg="#555555")

                # --- Hand UI (Updated with Shake Metrics) ---
                if self.hand_ai.engine_active:
                    hand_status = f"Gesture: {self.hand_ai.current_gesture}\nShake Intensity: {self.hand_ai.current_shake_metric:.0f}%"
                    txt_color = "#00ff00" 
                    if self.hand_ai.current_score == 100:
                        txt_color = "#ff4444" 
                    elif self.hand_ai.current_shake_metric > 40:
                        txt_color = "#FFA500" 
                        
                    self.lbl_hand.config(text=hand_status, fg=txt_color, justify=tk.LEFT)
                else:
                    self.lbl_hand.config(text="Gesture: DISABLED\nShake Intensity: N/A", fg="#555555", justify=tk.LEFT)

                if self.vitals_ai.engine_active:
                    if self.vitals_ai.is_connected:
                        self.lbl_vitals.config(text=f"Heart Rate: {self.vitals_ai.current_hr} BPM", fg="#ff4444" if self.vitals_ai.current_score == 100 else "#00ff00")
                    else:
                        self.lbl_vitals.config(text="Heart Rate: SEARCHING...", fg="#FFA500")
                else:
                    self.lbl_vitals.config(text="Heart Rate: DISABLED", fg="#555555")

                if not face_available and not vitals_available and not self.hand_ai.engine_active:
                    self.lbl_master.config(text="ALL SENSORS OFF", fg="#FFA500")
                    self.dash_frame.config(bg="#1e1e1e")
                elif final_distress > 80:
                    self.lbl_master.config(text=f"CRITICAL: {final_distress:.0f}%", fg="#ff4444")
                    self.dash_frame.config(bg="#2d0000") 
                    cv2.rectangle(frame, (0, 0), (img_w, img_h), (0, 0, 255), 10) 
                else:
                    self.lbl_master.config(text=f"MONITORING: {final_distress:.0f}%", fg="#00ff00")
                    self.dash_frame.config(bg="#1e1e1e") 
            
            else:
                self.lbl_face.config(text="Face Distress: PAUSED", fg="#aaaaaa")
                self.lbl_hand.config(text="Gesture: PAUSED\nShake Intensity: N/A", fg="#aaaaaa")
                self.lbl_vitals.config(text="Heart Rate: PAUSED", fg="#aaaaaa")
                self.lbl_master.config(text="PAUSED", fg="#aaaaaa")
                self.dash_frame.config(bg="#1e1e1e")
                cv2.putText(frame, "SYSTEM PAUSED", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (170, 170, 170), 2)

            cv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(cv_img)
            aspect_ratio = img_w / img_h
            new_width = 850
            new_height = int(new_width / aspect_ratio)
            pil_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
            
            imgtk = ImageTk.PhotoImage(image=pil_img)
            self.video_label.imgtk = imgtk 
            self.video_label.configure(image=imgtk)

        self.root.after(20, self.update_ui_loop)

    def on_closing(self):
        print("Initiating system shutdown...")
        self.cam.stop()
        self.face_ai.stop()
        self.hand_ai.stop()
        self.vitals_ai.stop()
        self.root.destroy()
        print("Shutdown complete.")

if __name__ == "__main__":
    root = tk.Tk()
    app = PatientMonitorApp(root)
    root.mainloop()