# space_check.py
import time
import config
import ultrasonic
import lift_motor
import rfid_reader

def _avg_ultra(samples=5, delay=0.05):
    readings = []
    for _ in range(samples):
        d = ultrasonic.read_distance()
        if d is not None:
            readings.append(d)
        time.sleep(delay)
    return sum(readings) / len(readings) if readings else None


def check_space_until_next_tag(end_tag, step_up_time=0.8, max_steps=25):
    ultrasonic.setup_ultrasonic()
    steps = 0

    while True:
        avg = _avg_ultra()
        print(f"[ULTRA] avg={avg}")

        if avg is None:
            return "SENSOR_FAIL"

        if avg > config.SPACE_THRESHOLD:
            lift_motor.stop()
            return "SPACE_OK"

        # No space → step up
        lift_motor.lift_up()
        time.sleep(step_up_time)
        lift_motor.stop()
        time.sleep(0.2)

        # Check end of shelf
        if end_tag is not None:
            tag = rfid_reader.read_tag_stable()
            if tag == end_tag:
                return "END_OF_SHELF"

        steps += 1
        if steps >= max_steps:
            return "END_OF_SHELF"
