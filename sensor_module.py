import RPi.GPIO as GPIO
import time
from cameraTest import capture_and_identify
import config

GPIO.setmode(GPIO.BCM)
GPIO.setup(config.IR_PIN, GPIO.IN)

def object_detected():
    """ترجع True إذا في جسم أمام الحساس"""
    signal = GPIO.input(config.IR_PIN)
    return signal == 0 if config.IR_ACTIVE_LOW else signal == 1

def start_sensor_loop():
    print("📡 Waiting for object...")
    try:
        while True:
            if object_detected():
                print("📘 Object detected! Starting recognition...")
                capture_and_identify()
                # انتظار خروج الجسم قبل الالتقاط التالي
                while object_detected():
                    time.sleep(0.1)
                print("✅ Done. Waiting for next object...")
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("🛑 Exiting...")
    finally:
        GPIO.cleanup()
