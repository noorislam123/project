import RPi.GPIO as GPIO
import time

# ===== PIN SETUP =====
IN3 = 17
IN4 = 27
ENA = 22   # PWM

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)
GPIO.setup(ENA, GPIO.OUT)

# ===== PWM =====
pwm = GPIO.PWM(ENA, 1000)   # 1 kHz
pwm.start(0)

try:
    print("🚀 Forward - MAX speed")
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm.ChangeDutyCycle(100)
    time.sleep(1)

    print("⏸ Stop")
    pwm.ChangeDutyCycle(0)
    time.sleep(1)

    print("⬅️ Backward - MAX speed")
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    pwm.ChangeDutyCycle(100)
    time.sleep(1)

    print("🛑 Stop")
    pwm.ChangeDutyCycle(0)

except KeyboardInterrupt:
    pass

finally:
    pwm.stop()
    GPIO.cleanup()
    print("✅ Test finished, GPIO cleaned")
