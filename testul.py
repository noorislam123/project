import RPi.GPIO as GPIO
import time

# --------------------------
# Pins (عدّليهم حسب توصيلك)
# --------------------------
TRIG = 23
ECHO = 24

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

print("Ultrasonic Test Started...")

try:
    while True:
        # Send Trigger pulse
        GPIO.output(TRIG, True)
        time.sleep(0.00001)   # 10 microseconds
        GPIO.output(TRIG, False)

        # Wait for Echo start
        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()

        # Wait for Echo end
        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()

        pulse_duration = pulse_end - pulse_start

        # Distance calculation
        distance = pulse_duration * 17150  # speed of sound / 2
        distance = round(distance, 2)

        print(f"Distance: {distance} cm")

        time.sleep(0.5)

except KeyboardInterrupt:
    print("Stopping...")
    GPIO.cleanup()
