import RPi.GPIO as GPIO
import time
import config
# ===== PIN SETUP =====
IN3 = 27
IN4 = 17
ENB = 22  # PWM


PWM_FREQ = 1000 # Hz

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)
GPIO.setup(ENB, GPIO.OUT)

pwm = GPIO.PWM(ENB, PWM_FREQ)
pwm.start(0)

def forward(speed):
    GPIO.output(IN3, 1)
    GPIO.output(IN4, 0)
    pwm.ChangeDutyCycle(speed)

def stop():
    pwm.ChangeDutyCycle(0)
    GPIO.output(IN3, 0)
    GPIO.output(IN4, 0)

def backward(speed):
    GPIO.output(IN3, 0)
    GPIO.output(IN4, 1)
    pwm.ChangeDutyCycle(speed)
try:
    print("FORCE DRIVE: 60% for 3 seconds...")
    forward(100)
    time.sleep(3)
    print("FORCE DRIVE: 60% for 3 seconds...")
    backward(100)
    time.sleep(3)

    print("STOP")
    stop()
    time.sleep(1)

finally:
    pwm.stop()
