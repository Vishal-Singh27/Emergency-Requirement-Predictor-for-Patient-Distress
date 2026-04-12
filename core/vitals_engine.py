import asyncio
import threading
from bleak import BleakScanner, BleakClient

class VitalsAnalyzer:
    def __init__(self):
        self.HEART_RATE_CHARACTERISTIC_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
        self.HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
        self.current_hr = 0
        self.current_score = 0
        self.is_connected = False
        self.is_running = False
        self.engine_active = False

    def start(self):
        self.is_running = True
        threading.Thread(target=self._worker, daemon=True).start()

    def stop(self):
        self.is_running = False

    def _hr_data_handler(self, sender, data):
        hr_format = data[0] & 0x01
        self.current_hr = data[1] if hr_format == 0 else int.from_bytes(data[1:3], byteorder='little')
        self.is_connected = True 
        
        if self.engine_active:
            if self.current_hr > 120 or self.current_hr < 40:
                self.current_score = 100
            elif self.current_hr > 100:
                self.current_score = 50 
            else:
                self.current_score = 0
        else:
            self.current_score = 0

    def _match_heart_rate_service(self, device, advertisement_data):
        return self.HEART_RATE_SERVICE_UUID.lower() in [uuid.lower() for uuid in advertisement_data.service_uuids]

    async def _connect_and_stream(self):
        print("[Vitals Engine] Scanning for Heart Rate broadcast...")
        target_device = await BleakScanner.find_device_by_filter(self._match_heart_rate_service, timeout=10.0)
        
        if target_device:
            print(f"[Vitals Engine] Connecting to device...")
            try:
                async with BleakClient(target_device) as client:
                    self.is_connected = True
                    await client.start_notify(self.HEART_RATE_CHARACTERISTIC_UUID, self._hr_data_handler)
                    while self.is_running:
                        await asyncio.sleep(1)
            except Exception as e:
                print(f"[Vitals Engine] Connection lost: {e}")
                self.is_connected = False
        else:
            print("[Vitals Engine] No broadcast found. Dynamic Fallback to Face-Only Mode.")
            self.is_connected = False

    def _worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._connect_and_stream())