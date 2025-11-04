import RPi.GPIO as GPIO
import time
import config

GPIO.setwarnings(False)  # 🔇 إيقاف التحذير
GPIO.setmode(GPIO.BCM)
GPIO.setup(config.RELAY_PIN, GPIO.OUT)

# تحديد نوع الريلاي
ACTIVE_HIGH = True  # غيّرها إلى False إذا الريلاي Active High

def conveyor_on():
    print("Relay ON (Conveyor running)")
    GPIO.output(config.RELAY_PIN, GPIO.HIGH if ACTIVE_HIGH else GPIO.LOW)

def conveyor_off():
    print("Relay OFF (Conveyor stopped)")
    GPIO.output(config.RELAY_PIN, GPIO.LOW if ACTIVE_HIGH else GPIO.HIGH)

def cleanup():
    GPIO.cleanup()
