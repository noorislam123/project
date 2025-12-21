import RPi.GPIO as GPIO
import time
import config

IN3 = 17
IN4 = 27
ENA = 22

def setup():
    GPIO.setup(IN3, GPIO.OUT)
    GPIO.setup(IN4, GPIO.OUT)
    GPIO.setup(ENA, GPIO.OUT)

    global pwm
    pwm = GPIO.PWM(ENA, 1000)
    pwm.start(0)

def forward(speed=100):
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm.ChangeDutyCycle(speed)

def stop():
    pwm.ChangeDutyCycle(0)

def run_until_micro_on_then_off():
    print("🚗 Drive motor started (waiting micro ON → OFF)")
    forward(100)

    # 1️⃣ ننتظر الكتاب يوصل (micro = ON)
    while GPIO.input(config.MICRO_PIN) == GPIO.LOW:
        time.sleep(0.01)

    print("📘 Micro switch ON (book detected)")

    # 2️⃣ ننتظر الكتاب يترك السويتش (micro = OFF)
    while GPIO.input(config.MICRO_PIN) == GPIO.HIGH:
        time.sleep(0.01)

    stop()
    print("🛑 Drive motor stopped (micro switch OFF after ON)")
