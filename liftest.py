import RPi.GPIO as GPIO
import time

# GPIO pins (BCM)
IN1 = 6
IN2 = 5

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)

def stop():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    print("⛔ Motor STOP")

def lift_up(duration=3):
    print("⬆️ Lifting UP")
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    time.sleep(duration)
    stop()

def lift_down(duration=3):
    print("⬇️ Lifting DOWN")
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    time.sleep(duration)
    stop()

try:
    print("🔧 Lift Motor Test Started")

    lift_up(11)
    time.sleep(1)


    lift_down(10)
    time.sleep(1)

    print("✅ Test finished successfully")

except KeyboardInterrupt:
    print("🛑 Test interrupted")

finally:
    stop()
    GPIO.cleanup()
    print("🧹 GPIO cleaned up")
