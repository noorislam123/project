import RPi.GPIO as GPIO
import time
import config

IN1 = 17
IN2 = 27
ENA = 22

def setup():
    GPIO.setup(IN1, GPIO.OUT)
    GPIO.setup(IN2, GPIO.OUT)
    GPIO.setup(ENA, GPIO.OUT)

    global pwm
    pwm = GPIO.PWM(ENA, 1000)
    pwm.start(0)

def forward(speed=100):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    pwm.ChangeDutyCycle(speed)

def backward(speed=100):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    pwm.ChangeDutyCycle(speed)

def stop():
    pwm.ChangeDutyCycle(0)

def run_until_micro_on():
    print("🚗 Drive motor ON (Ultrasonic OK)")
    forward(100)

    # ننتظر وصول الكتاب (micro يصير ON)
    while GPIO.input(config.MICRO_PIN) == GPIO.LOW:
        time.sleep(0.005)
        
    backward()
    time.sleep(1.5)
    stop()
    print("🛑 Drive motor OFF (micro switch ON)")
