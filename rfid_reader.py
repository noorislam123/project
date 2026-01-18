
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
from collections import Counter

# ✅ تهيئة القارئ مرة واحدة عند استيراد الملف
_reader = None
_debug_enabled = True

def setup():
    """تهيئة قارئ RFID"""
    global _reader
    try:
        _reader = SimpleMFRC522()
        _debug("✅ RFID Reader initialized successfully")
        return True
    except Exception as e:
        _debug(f"❌ RFID Reader initialization failed: {e}")
        return False

def _debug(msg):
    """طباعة رسالة debug"""
    global _debug_enabled
    if _debug_enabled:
        print(msg)

def set_debug(enabled=True):
    """تفعيل/تعطيل رسائل debug"""
    global _debug_enabled
    _debug_enabled = enabled

def read_once():
  
    global _reader
    if _reader is None:
        setup()
    
    try:
        # ✅ الحل: استخدام read_id_no_block بدلاً من read_no_block
        # read_id_no_block يقرأ فقط الـ ID بدون محاولة قراءة البيانات
        # هذا يمنع حدوث AUTH ERROR
        id = _reader.read_id_no_block()
        if id is not None:
            return int(id)
        return None
    except Exception as e:
        # نتجاهل الأخطاء البسيطة
        return None

def read_stable(stable_reads=3, window_s=0.5):
 
    global _reader
    if _reader is None:
        setup()
    
    readings = []
    start_time = time.time()
    
    while time.time() - start_time < window_s:
        tag = read_once()
        if tag is not None:
            readings.append(tag)
        time.sleep(0.05)
    
    if not readings:
        return None
    
    # إيجاد القيمة الأكثر تكراراً
    counter = Counter(readings)
    most_common_tag, count = counter.most_common(1)[0]
    
    # إذا تكررت القيمة بالعدد المطلوب، نعيدها
    if count >= stable_reads:
        return most_common_tag
    
    return None

def read_blocking(timeout=5.0):
    
    global _reader
    if _reader is None:
        setup()
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        tag = read_once()
        if tag is not None:
            return tag
        time.sleep(0.1)
    
    return None

def wait_for_tag(target_tag, timeout=10.0):
 
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        tag = read_stable()
        if tag == target_tag:
            return True
        time.sleep(0.1)
    
    return False

def cleanup():
    """تنظيف الموارد"""
    global _reader
    _reader = None
    # لا نقوم بـ GPIO.cleanup() هنا لأنه يتم في الكود الرئيسي

# ✅ تهيئة تلقائية عند استيراد الملف
setup()

# =========================
# TEST CODE
# =========================
if __name__ == "__main__":
    """كود اختبار الوحدة - بدون AUTH ERROR"""
    import signal
    
    def end_read(signal, frame):
        print("\n🛑 Stopping RFID reader...")
        GPIO.cleanup()
        exit()
    
    signal.signal(signal.SIGINT, end_read)
    
    print("=" * 50)
    print("🧪 RFID Reader Test Mode (NO AUTH ERROR)")
    print("=" * 50)
    print("\n📡 Bring your RFID tag close to the reader...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            # اختبار القراءة المستقرة
            tag = read_stable(stable_reads=3, window_s=0.5)
            
            if tag is not None:
                print(f"✅ Tag detected: {tag}")
                print("-" * 50)
                time.sleep(0.5)
            else:
                time.sleep(0.2)
    
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\n✅ Test completed")