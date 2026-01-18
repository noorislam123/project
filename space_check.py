# space_check.py
import RPi.GPIO as GPIO
import time
import config

TRIG_PIN = getattr(config, "TRIG_PIN", 23)
ECHO_PIN = getattr(config, "ECHO_PIN", 24)

# ✅ متغير للتحقق من التهيئة
_is_setup = False

def setup():
    """تهيئة الـ Ultrasonic"""
    global _is_setup
    try:
        GPIO.setup(TRIG_PIN, GPIO.OUT)
        GPIO.setup(ECHO_PIN, GPIO.IN)
        GPIO.output(TRIG_PIN, False)
        time.sleep(0.1)
        _is_setup = True
        print(f"✅ Ultrasonic initialized (TRIG={TRIG_PIN}, ECHO={ECHO_PIN})")
    except Exception as e:
        print(f"❌ Ultrasonic setup failed: {e}")
        _is_setup = False


def _ensure_setup():
    """التأكد من التهيئة قبل الاستخدام"""
    global _is_setup
    if not _is_setup:
        print("⚠️ Ultrasonic not setup, initializing now...")
        setup()


def get_distance():
    """قراءة المسافة"""
    # ✅ التأكد من التهيئة قبل الاستخدام
    _ensure_setup()
    
    try:
        GPIO.output(TRIG_PIN, False)
        time.sleep(0.01)
        
        GPIO.output(TRIG_PIN, True)
        time.sleep(0.00001)
        GPIO.output(TRIG_PIN, False)
        
        timeout = time.time() + 0.1
        pulse_start = time.time()
        while GPIO.input(ECHO_PIN) == 0:
            pulse_start = time.time()
            if time.time() > timeout:
                return None
        
        timeout = time.time() + 0.1
        pulse_end = time.time()
        while GPIO.input(ECHO_PIN) == 1:
            pulse_end = time.time()
            if time.time() > timeout:
                return None
        
        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150
        return distance
    except Exception as e:
        print(f"⚠️ Ultrasonic read error: {e}")
        return None


def check_space_fast(threshold=15, max_samples=3):
    """فحص سريع - يوقف أول ما يلقى space"""
    # ✅ التأكد من التهيئة
    _ensure_setup()
    
    print(f"[ULTRA] Checking (threshold={threshold} cm)")
    
    for i in range(max_samples):
        dist = get_distance()
        
        if dist is None:
            print(f"[ULTRA] sample {i+1}: timeout")
            time.sleep(0.03)
            continue
        
        print(f"[ULTRA] sample {i+1}: {dist:.2f} cm")
        
        if dist > threshold:
            print(f"[ULTRA] ✅ SPACE_OK")
            return "SPACE_OK"
        
        if i < max_samples - 1:
            time.sleep(0.03)
    
    print("[ULTRA] ❌ NO_SPACE")
    return "NO_SPACE"


def check_space(samples=1, delay=0.03, threshold=15):
    """للتوافق"""
    # ✅ التأكد من التهيئة
    _ensure_setup()
    
    return check_space_fast(threshold=threshold, max_samples=samples)