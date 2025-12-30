import RPi.GPIO as GPIO
import time
import config  # إذا عندك config فيه TRIG/ECHO pins

# إذا مش موجودين في config، عدليهم هنا
TRIG_PIN = getattr(config, "TRIG_PIN", 23)
ECHO_PIN = getattr(config, "ECHO_PIN", 24)

def setup_ultrasonic():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG_PIN, GPIO.OUT)
    GPIO.setup(ECHO_PIN, GPIO.IN)
    GPIO.output(TRIG_PIN, False)
    time.sleep(0.05)

def read_distance(timeout=0.02):
    """
    Returns distance in cm, or None on timeout/invalid reading.
    timeout: seconds (0.02 = 20ms ~ 3.4m range)
    """
    # Trigger pulse
    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)

    start_wait = time.time()

    # Wait for echo to go HIGH
    while GPIO.input(ECHO_PIN) == 0:
        if time.time() - start_wait > timeout:
            return None
    pulse_start = time.time()

    # Wait for echo to go LOW
    while GPIO.input(ECHO_PIN) == 1:
        if time.time() - pulse_start > timeout:
            return None
    pulse_end = time.time()

    duration = pulse_end - pulse_start
    distance_cm = (duration * 34300) / 2  # speed of sound 34300 cm/s

    # فلترة قراءات غير منطقية (اختياري)
    if distance_cm <= 0 or distance_cm > 400:
        return None

    return distance_cm
