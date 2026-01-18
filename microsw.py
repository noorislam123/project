import RPi.GPIO as GPIO
import time
import config

PIN = getattr(config, "MICRO_SWITCH_PIN", 26)
ACTIVE_LOW = getattr(config, "MICRO_ACTIVE_LOW", True)
DEBOUNCE = getattr(config, "MICRO_DEBOUNCE", 0.05)


def setup():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    pull = GPIO.PUD_UP if ACTIVE_LOW else GPIO.PUD_DOWN
    GPIO.setup(PIN, GPIO.IN, pull_up_down=pull)


def is_pressed() -> bool:
    v = GPIO.input(PIN)
    return (v == 0) if ACTIVE_LOW else (v == 1)


def wait_for_press(timeout=10.0) -> bool:
    t0 = time.time()

    # ⏳ تأكد إنه مش مضغوط من البداية
    while is_pressed():
        time.sleep(0.01)

    # ⏳ استنى الضغط الحقيقي
    while True:
        if is_pressed():
            time.sleep(DEBOUNCE)
            return True

        if timeout is not None and (time.time() - t0) > timeout:
            return False

        time.sleep(0.01)  # ✅ مهم جداً
