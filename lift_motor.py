# lift motor
import RPi.GPIO as GPIO
import time

IN1 = 6
IN2= 5

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(IN1, GPIO.OUT)
    GPIO.setup(IN2, GPIO.OUT)
    stop()

def lift_up():
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    print("⬆️ Lifting UP")

def lift_down():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    print("⬇️ Lifting DOWN")

def stop():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    print("⛔ Motor stopped")

def cleanup():
    GPIO.cleanup()
if __name__ == "__main__":
    setup()
    print("Testing lifting UP for 2 seconds...")
    lift_up()
    time.sleep(5)

    print("Testing lifting DOWN for 2 seconds...")
    lift_down()
    time.sleep(5)

    print("Stopping motor...")
    stop()

    GPIO.cleanup()


