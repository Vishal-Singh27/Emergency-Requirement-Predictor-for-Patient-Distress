# Multimodal Patient Distress Predictor (macOS Native)

A multithreaded, edge-AI telemetry dashboard built for macOS. This system actively monitors a patient's visual and physiological state by fusing computer vision heuristics with real-time Bluetooth Low Energy (BLE) vitals data. 

Built with an object-oriented architecture, this project demonstrates real-time sensor fusion with zero UI latency.

---

### 🧠 System Architecture

This application utilizes a **Late-Fusion Multimodal Architecture** spread across asynchronous background threads to ensure the main UI never bottlenecks while waiting for hardware reads or AI inferences.

* **The Vision Engine (Face):** Utilizes `DeepFace` via an optimized OpenCV pipeline. Implements rolling average buffers (`collections.deque`) and custom emotion weighting to filter out sensor noise and prevent false positives.
* **The Kinematic Engine (Hands):** Utilizes the `MediaPipe Tasks API` to track real-time wrist and digit landmarks, mapped against custom heuristic bounds to detect 1-hand and 2-hand choking gestures.
* **The Vitals Engine (BLE):** Utilizes `Bleak` and `asyncio` to interface directly with macOS `CoreBluetooth`. Dynamically scans for the globally standardized `180D` Heart Rate Service UUID to stream real-time BPM from an Apple Watch.
* **Dynamic Weighting System:** An autonomous fallback protocol that redistributes trust weights if a hardware sensor (like the Apple Watch) disconnects, ensuring uninterrupted monitoring via "Face-Only Mode."

---

### ⚙️ Installation & Usage (Developer Mode)

**Prerequisites:** Requires an Apple Silicon Mac running macOS 13+ (Ventura or newer).

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/yourusername/patient-distress-predictor.git](https://github.com/yourusername/patient-distress-predictor.git)
    cd patient-distress-predictor
    ```

2.  **Set up the environment and install dependencies:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Run the master application:**
    ```bash
    python main.py
    ```

---

### 📦 Building a Standalone macOS App

You can compile this Python project into a native `.app` executable using PyInstaller. This allows the dashboard to run without terminal commands.

Run this command from the root directory to bundle the app and the MediaPipe model weights:

```bash
pyinstaller --name "DistressMonitor" --windowed --noconsole --add-data "hand_landmarker.task:." main.py
```

Once finished, locate `DistressMonitor.app` in the generated `dist/` folder. You can move this directly to your Mac's `Applications` folder.

---

### 🛠️ Hardware Requirements

* **Camera:** Built-in Mac Webcam or an iPhone via macOS Continuity Camera.
* **Vitals:** Apple Watch running an active BLE Heart Rate broadcaster (e.g., Echo Heart Rate) without pairing directly to the Mac.

---

*Disclaimer: This is an exploratory MVP for edge-AI sensor fusion. It is not a certified medical device and should not be used for actual diagnostic, monitoring, or emergency response purposes.*