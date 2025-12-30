# drive_motor.py  (NO PWM - default speed + return back 1s)
import RPi.GPIO as GPIO
import time

# ===== PIN SETUP =====
IN3 = 17
IN4 = 27
ENB = 22   # Enable (ON/OFF)

def setup():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(IN3, GPIO.OUT)
    GPIO.setup(IN4, GPIO.OUT)
    GPIO.setup(ENB, GPIO.OUT)

    # Motor OFF at start
    GPIO.output(IN3, 0)
    GPIO.output(IN4, 0)
    GPIO.output(ENB, 0)

def forward():
    # Enable driver (default/full speed)
    GPIO.output(ENB, 1)
    GPIO.output(IN3, 1)
    GPIO.output(IN4, 0)

def backward():
    # Reverse direction (default/full speed)
    GPIO.output(ENB, 1)
    GPIO.output(IN3, 0)
    GPIO.output(IN4, 1)

def stop():
    # Disable driver + stop pins
    GPIO.output(IN3, 0)
    GPIO.output(IN4, 0)
    GPIO.output(ENB, 0)

def run_until_micro_release(
    micro_module,
    timeout=6.0,
    poll=0.01,
    min_run=0.20,
    back_time=1.0
):
    """
    يدفع الكتاب بسرعة الديفولت:
    - إذا micro ON من البداية: يستنى يصير OFF -> يوقف
    - إذا micro OFF: يستنى ON ثم OFF -> يوقف
    ثم يرجّع الدافع للخلف لمدة back_time (افتراضي 1 ثانية)
    """

    t0 = time.time()
    forward()

    start_pressed = micro_module.is_pressed()
    if start_pressed:
        print("🟢 DRIVE: micro already ON at start → wait for OFF")
        saw_on = True
    else:
        print("🟡 DRIVE: waiting for micro ON...")
        saw_on = False

    try:
        while True:
            elapsed = time.time() - t0
            pressed = micro_module.is_pressed()

            # لا توقف بسرعة جداً أول التشغيل
            if elapsed < min_run:
                time.sleep(poll)
                continue

            # إذا ما شفنا ON لسه، نستنى ON
            if not saw_on:
                if pressed:
                    saw_on = True
                    print("🟢 DRIVE: micro ON detected → now wait for OFF")
            else:
                # شفنا ON، الآن أول OFF يوقف
                if not pressed:
                    print("🔴 DRIVE: micro OFF detected → STOP")
                    break

            if elapsed > timeout:
                print("⚠️ DRIVE: timeout")
                break

            time.sleep(poll)

    finally:
        stop()

        # ↩️ رجوع بنفس مسافة الدفع تقريباً (1 ثانية)
        if back_time and back_time > 0:
            print(f"↩️ DRIVE: return back {back_time}s")
            backward()
            time.sleep(back_time)
            stop()
