import RPi.GPIO as GPIO
import time

MICRO_PIN = 26  # البن الموصول على المايكرو سويتش

def setup():
    """تجهيز البن للمايكرو سويتش"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(MICRO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    print("[MicroSwitch] Initialized on pin", MICRO_PIN)

def wait_for_press(timeout=17):
    """ينتظر ضغط المايكرو سويتش خلال مدة محددة"""
    start_time = time.time()
    while True:
        if GPIO.input(MICRO_PIN) == GPIO.LOW:
            print("🔴 Micro switch pressed.")
            return True
        if time.time() - start_time > timeout:
            print("❌ ERROR: Micro switch not pressed within 17 seconds!")
            return False
        time.sleep(0.1)
