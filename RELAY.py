import RPi.GPIO as GPIO
import time

RELAY_PIN = 5

GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)

def conveyor_on():
    GPIO.output(RELAY_PIN, GPIO.HIGH)
    print("✅ Conveyor ON")

def conveyor_off():
    GPIO.output(RELAY_PIN, GPIO.LOW)
    print("🛑 Conveyor OFF")

try:
    while True:
        conveyor_on()
        time.sleep(10)
        conveyor_off()
        time.sleep(10)
except KeyboardInterrupt:
    GPIO.cleanup()

