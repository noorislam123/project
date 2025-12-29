#drive motor
import RPi.GPIO as GPIO
import time
import config

IN3 = 17
IN4 = 27
ENB = 22

def setup():
    GPIO.setup(IN3, GPIO.OUT)
    GPIO.setup(IN4, GPIO.OUT)
    GPIO.setup(ENB, GPIO.OUT)

    global pwm
    pwm = GPIO.PWM(ENB, 1000)
    pwm.start(0)

def forward(speed=100):
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm.ChangeDutyCycle(speed)

def backward(speed=100):
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
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


