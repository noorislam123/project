import RPi.GPIO as GPIO
import time
import config
# ===== PIN SETUP =====
IN3 = 17
IN4 = 27
ENB = 22   # PWM

PWM_FREQ = getattr(config, "PWM_FREQ", 1000)  # 1kHz مناسب غالبًا

_pwm = None


def setup():
    global _pwm
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(IN3, GPIO.OUT)
    GPIO.setup(IN4, GPIO.OUT)
    GPIO.setup(ENB, GPIO.OUT)

    GPIO.output(IN3, 0)
    GPIO.output(IN4, 0)

    _pwm = GPIO.PWM(ENB, PWM_FREQ)
    _pwm.start(0)


def _set_pwm(duty):
    duty = max(0, min(100, int(duty)))
    _pwm.ChangeDutyCycle(duty)


def forward(speed):
    GPIO.output(IN3, 1)
    GPIO.output(IN4, 0)
    _set_pwm(speed)


def stop():
    _set_pwm(0)
    GPIO.output(IN3, 0)
    GPIO.output(IN4, 0)


def run_until_micro_release(
    micro_module,
    speed=70,
    kick_speed=95,
    kick_time=0.25,
    timeout=6.0,
    poll=0.01,
    min_run=0.20
):
    """
    يدفع الكتاب:
    - kick start لتجاوز عزم البداية
    - يستنى micro ON (لو كان OFF)
    - بعد ما يصير ON، يستنى OFF -> يوقف
    - لو micro كان ON من البداية: يعتبر أنه "بدأ" ويستنى OFF مباشرة
    """

    t0 = time.time()

    # 🚀 Kick to overcome stiction
    forward(kick_speed)
    time.sleep(kick_time)

    # ➡️ Normal speed
    forward(speed)

    # حالة البداية
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
                # وما منوقف هون
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
