import RPi.GPIO as GPIO
import time
import config

# إعداد البن المستخدم
MICRO_PIN = 26

GPIO.setmode(GPIO.BCM)
GPIO.setup(config.MICRO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # باستخدام مقاومة سحب داخليّة

print("🧭 Waiting for micro switch signal...")

try:
    while True:
        if GPIO.input(config.MICRO_PIN) == GPIO.LOW:
            print("🔴 Micro switch PRESSED (Limit reached!)")
            time.sleep(0.5)
        else:
            print("🟢 Released")
            time.sleep(0.5)
except KeyboardInterrupt:
    GPIO.cleanup()
    print("GPIO Cleaned up")
        