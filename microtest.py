import RPi.GPIO as GPIO
import time

PIN = 26  # BCM

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Live read on GPIO26 (BCM). Ctrl+C to exit.")
print("Expect: released=1, pressed=0 (wired to GND)\n")

try:
    while True:
        v = GPIO.input(PIN)
        print("GPIO26 =", v, "->", ("RELEASED" if v == 1 else "PRESSED"))
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    GPIO.cleanup()
