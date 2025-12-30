# space_check.py
import time
import config
import ultrasonic

def _avg_ultra(samples=5, delay=0.05):
    readings = []
    for i in range(samples):
        d = ultrasonic.read_distance()
        print(f"[ULTRA] sample {i+1}/{samples}: {d} cm")
        if d is not None:
            readings.append(d)
        time.sleep(delay)
    return sum(readings) / len(readings) if readings else None

def check_space(samples=3, delay=0.03):
    ultrasonic.setup_ultrasonic()
    avg = _avg_ultra(samples=samples, delay=delay)
    print(f"[ULTRA] avg={avg} | threshold={config.SPACE_THRESHOLD} cm")

    if avg is None:
        print("[ULTRA] ❌ SENSOR_FAIL")
        return "SENSOR_FAIL"

    if avg > config.SPACE_THRESHOLD:
        print("[ULTRA] ✅ SPACE_OK")
        return "SPACE_OK"

    print("[ULTRA] ❌ NO_SPACE")
    return "NO_SPACE"
