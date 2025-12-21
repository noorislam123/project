import RPi.GPIO as GPIO
import time

TRIG = 23
ECHO = 24

def setup_ultrasonic():
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.output(TRIG, False)
    time.sleep(0.1)


def read_distance():

    # --- Trigger Pulse ---
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    # --- Wait for Echo HIGH ---
    timeout = time.time() + 0.05  # 50 ms
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if time.time() > timeout:
            return None    # NO SIGNAL RECEIVED

    # --- Wait for Echo LOW ---
    timeout = time.time() + 0.05
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if time.time() > timeout:
            return None

    # --- Calculate Distance ---
    duration = pulse_end - pulse_start
    distance = duration * 17150   # cm

    return round(distance, 2)
