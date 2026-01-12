import RPi.GPIO as GPIO
import time
import csv
import config
import RELAY
import microsw as micro_switch
import lift_motor
import rfid_reader
import space_check
import drive_motor

from cameraTest import capture_and_identify, load_database, load_features

# =========================
# LCD INIT
# =========================
_lcd = None
def _debug(msg: str):
    if getattr(config, "DEBUG", True):
        print(msg)

def lcd_init():
    global _lcd
    try:
        from RPLCD.i2c import CharLCD
        addr = getattr(config, "LCD_I2C_ADDR", 0x27)
        _lcd = CharLCD(
            i2c_expander="PCF8574",
            address=addr,
            port=1,
            cols=16,
            rows=2,
            charmap="A02",
            auto_linebreaks=False
        )
        _lcd.clear()
        lcd_show("System Ready", "Insert Book")
        _debug(f"[LCD] OK addr={hex(addr)}")
    except Exception as e:
        _lcd = None
        print(f"[LCD] init failed: {e}")

def lcd_show(line1="", line2="", delay=0.7):
    global _lcd
    l1 = str(line1)[:16].ljust(16)
    l2 = str(line2)[:16].ljust(16)
    if _lcd is None:
        _debug(f"[LCD-FALLBACK] {l1.strip()} | {l2.strip()}")
        time.sleep(delay)
        return
    try:
        _lcd.clear()
        _lcd.cursor_pos = (0, 0)
        _lcd.write_string(l1)
        _lcd.cursor_pos = (1, 0)
        _lcd.write_string(l2)
        time.sleep(delay)
    except Exception as e:
        _debug(f"[LCD] write failed: {e}")

# =========================
# GPIO INIT
# =========================
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(config.IR_PIN, GPIO.IN)

micro_switch.setup()
lift_motor.setup()
drive_motor.setup()
lcd_init()

def object_detected():
    signal = GPIO.input(config.IR_PIN)
    return signal == 0 if config.IR_ACTIVE_LOW else signal == 1

def build_shelf_tag_map():
    shelf_to_tag = {}
    with open(config.DB_FILE, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            shelf_to_tag[int(row["Shelf"])] = int(row["RFID_Tag"])
    return shelf_to_tag

def get_next_shelf_tag(current_shelf, shelf_to_tag):
    shelves = sorted(shelf_to_tag.keys())
    if current_shelf not in shelf_to_tag:
        return None
    i = shelves.index(current_shelf)
    if i == len(shelves) - 1:
        return getattr(config, "END_TAG", None)
    return shelf_to_tag[shelves[i + 1]]

# =========================
# SENSOR LOOP
# =========================
def start_sensor_loop():
    lcd_show("System Ready", "Insert Book")
    _debug("📡 System ON → Waiting for object (IR)...")

    # Load DB
    try:
        books_db = load_database()
        features_db = load_features()
        shelf_to_tag = build_shelf_tag_map()
        lcd_show("Database Loaded", "Ready")
        _debug(f"🗺️ Shelf map loaded: {shelf_to_tag}")
        time.sleep(0.8)
    except Exception as e:
        _debug(f"❌ DB load error: {e}")
        books_db = {}
        features_db = {}
        shelf_to_tag = {}
        lcd_show("DB Error", "Check CSV")
        time.sleep(1.2)

    home_tag = int(config.HOME_TAG)

    try:
        while True:
            lcd_show("System Ready", "Insert Book")
            if not object_detected():
                time.sleep(0.05)
                continue

            lcd_show("Book Detected", "Processing...")
            _debug("\n==============================")
            _debug("1️⃣ IR: Object detected ✅")
            _debug("==============================")
            time.sleep(0.3)

            # CAMERA
            lcd_show("Capturing Image", "Please Wait")
            _debug("2️⃣ CAMERA: Capturing frame...")
            try:
                found, book_folder, shelf, target_tag, used_barcode = capture_and_identify(books_db, features_db)
            except Exception as e:
                _debug(f"⚠️ CAMERA ERROR: {e}")
                found, book_folder, shelf, target_tag, used_barcode = False, None, None, None, False

            # الرسائل حسب الطريقة
            if found:
                if used_barcode:
                    lcd_show("Book Found", f"Shelf: {shelf}")
                    _debug(f"✅ Barcode recognized → Shelf {shelf}")
                else:
                    lcd_show("Book Found", f"AKAZE used → Shelf {shelf}")
                    _debug(f"✅ AKAZE recognized → Shelf {shelf}")
            else:
                if used_barcode:
                    lcd_show("Barcode not in DB", "Trying AKAZE")
                    _debug("❌ Barcode not found → fallback to AKAZE")
                else:
                    lcd_show("Book Unknown", "Try Again")
                    _debug("❌ Book not recognized by AKAZE")

                # انتظر إزالة الكتاب قبل العودة
                while object_detected():
                    time.sleep(0.05)
                continue

            # -------- RELAY + MICRO SWITCH --------
            lcd_show("Positioning", f"Shelf: {shelf}")
            _debug("3️⃣ RELAY+CONVEYOR: ON")
            RELAY.conveyor_on()

            lcd_show("Waiting MicroSwitch", "Book...")
            _debug("4️⃣ MICRO SWITCH: waiting press...")
            reached = micro_switch.wait_for_press(timeout=17.5)
            RELAY.conveyor_off()
            _debug("3️⃣ RELAY+CONVEYOR: OFF (safety)")

            if not reached:
                lcd_show("Position Failed", "Try Again")
                _debug("❌ Micro switch timeout → abort")
                while object_detected():
                    time.sleep(0.05)
                continue

            lcd_show("Book Positioned", f"Shelf: {shelf}")
            _debug("✅ Micro switch pressed → book positioned")
            time.sleep(0.5)

            # -------- LIFT + ULTRASONIC --------
            lcd_show("Lifting Book", "Please Wait")
            lift_motor.lift_up()

            scanning_started = False
            space_found = False
            shelf_full = False
            MAX_LIFT_TIME = 11
            ULTRA_INTERVAL = 0.6
            EXTRA_LIFT_AFTER_SPACE = 1.0
            space_time = None
            t0 = time.time()
            last_tag_print = None
            last_ultra_check = time.time()
            SPACE_OK_CONFIRM = 1
            space_ok_count = 0
            target_time = None
            MIN_AFTER_TARGET_DELAY = 0.4

            while True:
                if time.time() - t0 > MAX_LIFT_TIME:
                    _debug("🛑 Safety: max lift time reached → stop")
                    lcd_show("Lift Timeout", "Stopping...")
                    break

                tag = rfid_reader.read_tag_stable()
                if tag is not None and tag != last_tag_print:
                    _debug(f"🏷️ RFID: {tag}")
                    last_tag_print = tag

                if (not scanning_started) and (tag == target_tag):
                    scanning_started = True
                    target_time = time.time()
                    last_ultra_check = time.time()
                    space_ok_count = 0
                    lcd_show("Target Reached", "Checking Space")
                    _debug("✅ TARGET reached → ultrasonic ON")

                if scanning_started and (not space_found):
                    if target_time is not None and (time.time() - target_time < MIN_AFTER_TARGET_DELAY):
                        time.sleep(0.02)
                        continue

                    if time.time() - last_ultra_check >= ULTRA_INTERVAL:
                        last_ultra_check = time.time()
                        lcd_show("Checking Space", "Please Wait")
                        res = space_check.check_space(samples=3, delay=0.03)
                        if res == "SPACE_OK":
                            space_ok_count += 1
                            lcd_show("Space Found!", f"Placing Book")
                            if space_ok_count >= SPACE_OK_CONFIRM:
                                space_found = True
                                space_time = time.time()
                        else:
                            space_ok_count = 0
                            lcd_show("No Space Yet", "Searching...")

                if space_found and space_time is not None:
                    if time.time() - space_time >= EXTRA_LIFT_AFTER_SPACE:
                        lcd_show("Position Set", "Stopping Lift")
                        break

                time.sleep(0.02)

            lift_motor.stop()
            time.sleep(0.5)

            if space_found:
                lcd_show("Shelving Book", "Please Wait")
                drive_motor.run_until_micro_release(micro_switch, timeout=6.0)
                lcd_show("Book Shelved!", f"Shelf: {shelf}")
            else:
                lcd_show("No Space", "Returning...")

            # -------- RETURN HOME --------
            lcd_show("Returning", "To Home")
            lift_motor.lift_down()
            td = time.time()
            while True:
                t = rfid_reader.read_tag_stable()
                if t == home_tag:
                    lcd_show("Home Reached", "Ready Soon")
                    time.sleep(0.5)
                    lift_motor.stop()
                    break
                if time.time() - td > 25:
                    lcd_show("Home Timeout", "Stopped")
                    lift_motor.stop()
                    break
                time.sleep(0.05)

            lcd_show("System Ready", "Next Book")
            while object_detected():
                time.sleep(0.05)

    except KeyboardInterrupt:
        _debug("🛑 Exiting system...")
        lcd_show("System Stopped", "Bye!")

    finally:
        _debug("🔻 Safety shutdown")
        lcd_show("Safety Mode", "Shutting Down")
        RELAY.conveyor_off()
        lift_motor.stop()
        GPIO.cleanup()
        if _lcd:
            _lcd.clear()
        _debug("GPIO cleaned up.")


if __name__ == "__main__":
    start_sensor_loop()
