import RPi.GPIO as GPIO
import time
import csv
import config
import RELAY
import microsw as micro_switch
import lift_motor
import space_check
import drive_motor

from mfrc522 import SimpleMFRC522
from collections import Counter
from cameraTest import capture_and_identify, load_database, load_features

# =========================
# RFID READER MODULE (OPTIMIZED - FAST)
# =========================
class RFIDReader:
    """وحدة قراءة RFID محسّنة للسرعة - بدون AUTH ERROR"""
    
    def __init__(self):
        self.reader = None
        self.setup()
    
    def setup(self):
        """تهيئة قارئ RFID"""
        try:
            self.reader = SimpleMFRC522()
            self._debug("✅ RFID Reader initialized successfully")
            return True
        except Exception as e:
            self._debug(f"❌ RFID Reader initialization failed: {e}")
            return False
    
    def read_once(self):
        """قراءة Tag واحدة فورية - بدون AUTH ERROR"""
        if self.reader is None:
            self.setup()
        
        try:
            id = self.reader.read_id_no_block()
            if id is not None:
                return int(id)
            return None
        except Exception as e:
            return None
    
    def read_stable(self, stable_reads=2, window_s=0.25):
        
        readings = []
        start_time = time.time()
        last_tag = None
        same_count = 0
        
        while time.time() - start_time < window_s:
            tag = self.read_once()
            
            if tag is not None:
                readings.append(tag)
                
                # ✅ Early exit - لو قرأ نفس الـ tag متتالياً
                if tag == last_tag:
                    same_count += 1
                    if same_count >= stable_reads:
                        return tag  # ← يطلع فوراً بدون انتظار!
                else:
                    last_tag = tag
                    same_count = 1
            
            time.sleep(0.02)  # ← أسرع من 0.05
        
        if not readings:
            return None
        
        # Fallback - لو ما لقى متتالية
        counter = Counter(readings)
        most_common_tag, count = counter.most_common(1)[0]
        if count >= stable_reads:
            return most_common_tag
        
        return None
    
    def read_fast(self):
        """قراءة سريعة جداً - بدون تحقق (للحالات السريعة)"""
        return self.read_once()
    
    def _debug(self, msg):
        """طباعة رسالة debug"""
        if getattr(config, "DEBUG", True):
            print(msg)


# =========================
# LCD MODULE
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
    """طباعة رسالة على LCD مع delay محدد"""
    global _lcd
    l1 = str(line1)[:16].ljust(16)
    l2 = str(line2)[:16].ljust(16)
    if _lcd is None:
        _debug(f"[LCD-FALLBACK] {l1.strip()} | {l2.strip()}")
        if delay: time.sleep(delay)
        return
    try:
        _lcd.clear()
        _lcd.cursor_pos = (0, 0)
        _lcd.write_string(l1)
        _lcd.cursor_pos = (1, 0)
        _lcd.write_string(l2)
        if delay: time.sleep(delay)
    except Exception as e:
        _debug(f"[LCD] write failed: {e}")


# =========================
# GPIO INIT
# =========================
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(config.IR_PIN, GPIO.IN)

# Initialize modules
micro_switch.setup()
lift_motor.setup()
drive_motor.setup()
space_check.setup()
lcd_init()

# Initialize RFID Reader
_debug("📡 Initializing RFID Reader...")
rfid = RFIDReader()

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
    """الحصول على tag الرف التالي"""
    shelves = sorted(shelf_to_tag.keys())
    if current_shelf not in shelf_to_tag:
        return None
    i = shelves.index(current_shelf)
    if i == len(shelves) - 1:
        return getattr(config, "END_TAG", None)
    return shelf_to_tag[shelves[i + 1]]

# =========================
# SENSOR LOOP - OPTIMIZED
# =========================
def start_sensor_loop():
    lcd_show("System Ready", "Insert Book", delay=0.5)
    _debug("📡 System ON → Waiting for object (IR)...")

    # -------- Load DB --------
    try:
        books_db = load_database()
        features_db = load_features()
        shelf_to_tag = build_shelf_tag_map()
        lcd_show("Database Loaded", "Ready", delay=1.0)
        _debug(f"🗺️ Shelf map loaded: {shelf_to_tag}")
    except Exception as e:
        _debug(f"❌ DB load error: {e}")
        books_db = {}
        features_db = {}
        shelf_to_tag = {}
        lcd_show("DB Error", "Check CSV", delay=1.2)

    home_tag = int(config.HOME_TAG)

    try:
        while True:
            lcd_show("System Ready", "Insert Book", delay=0.5)
            if not object_detected():
                time.sleep(0.05)
                continue

            # -------- Detection Messages --------
            lcd_show("Book Detected", "Processing...", delay=0.5)
            _debug("1️⃣ IR: Object detected ✅")

            lcd_show("Capturing Image", "Please Wait", delay=0.8)
            _debug("2️⃣ CAMERA: Capturing frame...")

            try:
                found, book_folder, shelf, target_tag, used_barcode = capture_and_identify(books_db, features_db)
            except Exception as e:
                _debug(f"⚠️ CAMERA ERROR: {e}")
                found, book_folder, shelf, target_tag, used_barcode = False, None, None, None, False

            # -------- Result Messages --------
            if found:
                if used_barcode:
                    lcd_show("Book Found", f"Shelf: {shelf}", delay=1.2)
                    _debug(f"✅ Barcode recognized → Shelf {shelf}")
                else:
                    lcd_show("Book Found", f"AKAZE → Shelf {shelf}", delay=1.2)
                    _debug(f"✅ AKAZE recognized → Shelf {shelf}")
            else:
                if used_barcode:
                    lcd_show("Barcode not in DB", "Trying AKAZE", delay=1.0)
                    _debug("❌ Barcode not found → fallback to AKAZE")
                else:
                    lcd_show("Book Unknown", "Try Again", delay=1.0)
                    _debug("❌ Book not recognized by AKAZE")

                while object_detected():
                    time.sleep(0.05)
                continue

            # -------- Conveyor + MicroSwitch --------
            lcd_show("Positioning", f"Shelf: {shelf}", delay=0.7)
            RELAY.conveyor_on()

            lcd_show("Waiting MicroSwitch", "Book...", delay=0.7)
            reached = micro_switch.wait_for_press(timeout=17.5)
            RELAY.conveyor_off()

            if not reached:
                lcd_show("Position Failed", "Try Again", delay=1.0)
                _debug("❌ Micro switch timeout → abort")
                while object_detected():
                    time.sleep(0.05)
                continue

            lcd_show("Book Positioned", f"Shelf: {shelf}", delay=1.0)
            _debug("✅ Micro switch pressed → book positioned")

            # ========================================
            # ✅ OPTIMIZED LOGIC: Lift + Space Check
            # ========================================
            
            next_shelf_tag = get_next_shelf_tag(shelf, shelf_to_tag)
            _debug(f"📍 Target: {target_tag}, Next: {next_shelf_tag}")
            
            lcd_show("Lifting Book", "To Shelf", delay=0.7)
            lift_motor.lift_up()
            
            # ========== Phase 1: البحث السريع عن الرف ==========
            _debug("🔍 Phase 1: Fast search for target shelf...")
            MAX_LIFT_TIME = 30
            start_time = time.time()
            target_found = False
            last_tag_print = None
            
            while time.time() - start_time < MAX_LIFT_TIME:
                # ✅ قراءة سريعة
                tag = rfid.read_fast()
                
                if tag == target_tag:
                    # تأكيد بقراءة stable
                    confirm = rfid.read_stable(stable_reads=2, window_s=0.2)
                    if confirm == target_tag:
                        target_found = True
                        _debug(f"✅ Target shelf {shelf} reached!")
                        lcd_show("Target Reached!", f"Shelf: {shelf}", delay=0.8)
                        break
                
                if tag is not None and tag != last_tag_print:
                    _debug(f"🏷️ RFID: {tag}")
                    last_tag_print = tag
                
                time.sleep(0.02)  # ← أسرع!
            
            if not target_found:
                lcd_show("Shelf Not Found", "Returning...", delay=1.0)
                _debug("❌ Target shelf not found - aborting")
                lift_motor.stop()
                
                # العودة للـ home
                lcd_show("Returning", "To Home", delay=0.7)
                lift_motor.lift_down()
                
                start_time = time.time()
                while time.time() - start_time < 30:
                    tag = rfid.read_stable(stable_reads=2, window_s=0.2)
                    if tag == home_tag:
                        lift_motor.stop()
                        break
                    time.sleep(0.05)
                else:
                    lift_motor.stop()
                
                while object_detected():
                    time.sleep(0.05)
                continue
            
            # ========== Phase 2: فحص المساحة والرفع التدريجي ==========
            _debug("🔍 Phase 2: Space check and gradual lift...")
            lift_motor.stop()
            time.sleep(0.3)
            
            space_found = False
            max_attempts = 20
            
            for attempt in range(max_attempts):
                lcd_show("Checking Space", f"Try {attempt+1}", delay=0.4)
                _debug(f"🔍 Attempt {attempt+1}/{max_attempts}")
                
                # فحص المساحة
                res = space_check.check_space(samples=3, delay=0.03)
                
                if res == "SPACE_OK":
                    space_found = True
                    lcd_show("Space Found!", "Placing Book", delay=0.8)
                    _debug("✅ Space found!")
                    break
                
                # ✅ قراءة سريعة للـ tag الحالي
                current_tag = rfid.read_stable(stable_reads=2, window_s=0.2)
                if current_tag == next_shelf_tag:
                    lcd_show("Next Shelf", "No Space", delay=1.0)
                    _debug(f"⚠️ Reached next shelf ({next_shelf_tag})")
                    break
                
                # ارفع
                lcd_show("No Space", "Lifting...", delay=0.3)
                _debug("⬆️ Lifting 0.8s...")
                lift_motor.lift_up()
                time.sleep(0.8)  # ← أسرع من 1.0
                lift_motor.stop()
                time.sleep(0.2)  # ← أسرع من 0.3
            
            lift_motor.stop()
            time.sleep(0.5)
            
            # ========== Phase 3: دفع أو عودة ==========
            if space_found:
                lcd_show("Shelving Book", "Please Wait", delay=0.8)
                _debug("📚 Pushing book...")
                drive_motor.run_until_micro_release(micro_switch, timeout=6.0)
                lcd_show("Book Shelved!", f"Shelf: {shelf}", delay=1.2)
                _debug(f"✅ Book shelved at {shelf}")
            else:
                lcd_show("No Space", "Returning...", delay=1.0)
                _debug("❌ No space found")

            # ========== Return Home ==========
            lcd_show("Returning", "To Home", delay=0.7)
            _debug("🏠 Returning to home...")
            lift_motor.lift_down()
            
            start_time = time.time()
            MAX_RETURN_TIME = 30
            
            while time.time() - start_time < MAX_RETURN_TIME:
                # ✅ قراءة سريعة
                tag = rfid.read_stable(stable_reads=2, window_s=0.2)
                
                if tag == home_tag:
                    lcd_show("Home Reached", "Ready!", delay=0.5)
                    _debug("✅ Home reached")
                    lift_motor.stop()
                    break
                
                if tag is not None:
                    _debug(f"🏷️ RFID: {tag}")
                
                time.sleep(0.02)  # ← أسرع
            else:
                lcd_show("Home Timeout", "Stopped", delay=1.0)
                _debug("⚠️ Home timeout")
                lift_motor.stop()

            # انتظار إزالة الكتاب
            lcd_show("System Ready", "Next Book", delay=0.5)
            while object_detected():
                time.sleep(0.05)

    except KeyboardInterrupt:
        lcd_show("System Stopped", "Bye!", delay=1.0)
        _debug("🛑 Exiting system...")

    finally:
        lcd_show("Safety Mode", "Shutting Down", delay=1.0)
        _debug("🔻 Safety shutdown")
        RELAY.conveyor_off()
        lift_motor.stop()
        GPIO.cleanup()
        if _lcd:
            _lcd.clear()
        _debug("GPIO cleaned up.")


if __name__ == "__main__":
    start_sensor_loop()