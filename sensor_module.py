import RPi.GPIO as GPIO
import time
from cameraTest import capture_and_identify
import config
import RELAY
import microsw as micro_switch

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(config.IR_PIN, GPIO.IN)
micro_switch.setup()  # إعداد المايكرو سويتش

def object_detected():
    """Return True if an object is detected by the IR sensor"""
    signal = GPIO.input(config.IR_PIN)
    return signal == 0 if config.IR_ACTIVE_LOW else signal == 1

def start_sensor_loop():
    print("📡 Waiting for object...")
    try:
        while True:
            if object_detected():
                print("📘 Object detected! Waiting 3 seconds before capture...")
                time.sleep(3)

                found = False
                try:
                    print("📸 Capturing and identifying the book...")
                    found = capture_and_identify()
                except Exception as e:
                    print(f"⚠️ Recognition error: {e}")
                    found = False

                print(f"[DEBUG] capture_and_identify() returned: {found}")

                print("⏳ Waiting 3 seconds before activating conveyor...")
                time.sleep(3)

                if found:
                    print("✅ Book recognized! Turning conveyor ON...")
                    RELAY.conveyor_on()

                    reached = micro_switch.wait_for_press(timeout=17.5)
                    if reached:
                        print("⏳ Waiting 2 seconds before stopping conveyor...")
                        time.sleep(2)
                        RELAY.conveyor_off()
                        print("🛑 Conveyor stopped (micro switch pressed)")
                    else:
                        RELAY.conveyor_off()
                        print("❌ ERROR: Book did not reach micro switch in time!")

                else:
                    print("❌ No match found. Conveyor stays OFF")

                while object_detected():
                    time.sleep(0.1)
                print("⏳ Done. Waiting for next object...")

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("🛑 Exiting...")
    finally:
        RELAY.conveyor_off()
        GPIO.cleanup()
        print("GPIO cleaned up.")
