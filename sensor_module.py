import RPi.GPIO as GPIO
import time
from cameraTest import capture_and_identify
import config
import RELAY
import microsw as micro_switch
import lift_motor
import rfid_reader    

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(config.IR_PIN, GPIO.IN)

micro_switch.setup()
lift_motor.setup()


def object_detected():
    """Return True if an object is detected by the IR sensor"""
    signal = GPIO.input(config.IR_PIN)
    return signal == 0 if config.IR_ACTIVE_LOW else signal == 1


def start_sensor_loop():
    print("📡 Waiting for object...")
    try:
        while True:

            # -----------------------------
            # 1) IR DETECT
            # -----------------------------
            if object_detected():
                print("📘 Object detected! Waiting 3 seconds before capture...")
                time.sleep(3)

                # -----------------------------
                # 2) CAMERA IDENTIFICATION
                # -----------------------------
                try:
                    print("📸 Capturing and identifying the book...")
                    found, book_folder, shelf, rfid_tag = capture_and_identify()
                except Exception as e:
                    print(f"⚠️ Recognition error: {e}")
                    found, book_folder, shelf, rfid_tag = False, None, None, None

                print(f"[DEBUG] capture_and_identify() → found={found}, folder={book_folder}, shelf={shelf}, RFID={rfid_tag}")

                print("⏳ Waiting 3 seconds before activating conveyor...")
                time.sleep(3)

                # -----------------------------
                # 3) IF RECOGNIZED → CONVEYOR
                # -----------------------------
                if found:
                    print("✅ Book recognized! Turning conveyor ON...")
                    RELAY.conveyor_on()

                    reached = micro_switch.wait_for_press(timeout=17.5)
                    if reached:
                        print("⏳ Waiting 2 seconds before stopping conveyor...")
                        time.sleep(2)
                        RELAY.conveyor_off()
                        print("🛑 Conveyor stopped (micro switch pressed)")

                        # ====================================================================
                        # 4) LIFT + RFID BASED ON BOOK DATABASE (The REAL correct logic)
                        # ====================================================================

                        print(f"📌 Book on shelf {shelf} → expecting RFID tag: {rfid_tag}")
                        print("⬆️ Starting lift motor...")
                        lift_motor.lift_up()

                        found_tag = False
                        attempts = 3

                        for i in range(attempts):
                            print(f"🔎 RFID attempt {i+1} of {attempts}...")
                            tag = rfid_reader.read_tag()
                            print(f"[DEBUG] Read tag: {tag}")

                            if tag is not None and tag == rfid_tag:
                                print("🎯 Correct RFID tag detected → stopping lift.")
                                lift_motor.stop()
                                found_tag = True
                                break
                            else:
                                print("❌ Wrong tag or no tag")

                            time.sleep(0.7)

                        if not found_tag:
                            print("⌛ No correct tag → lifting 2 more seconds...")
                            time.sleep(2)
                            lift_motor.stop()

                        print("⛔ Lift motor stopped")
                        # ====================================================================

                    else:
                        RELAY.conveyor_off()
                        print("❌ ERROR: Book did not reach micro switch in time!")

                else:
                    print("❌ No match found. Conveyor stays OFF")

                # Wait IR to reset
                while object_detected():
                    time.sleep(0.1)

                print("⏳ Ready for next object...")

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("🛑 Exiting...")

    finally:
        RELAY.conveyor_off()
        lift_motor.stop()
        GPIO.cleanup()
        print("GPIO cleaned up.")
