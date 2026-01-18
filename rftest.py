# rfid_reader.py
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
from collections import Counter

# ✅ تهيئة القارئ مرة واحدة عند استيراد الملف
_reader = None

def setup():
    """تهيئة قارئ RFID"""
    global _reader
    try:
        _reader = SimpleMFRC522()
        print("✅ RFID Reader initialized successfully")
        return True
    except Exception as e:
        print(f"❌ RFID Reader initialization failed: {e}")
        return False

def read_tag_once():
    """قراءة Tag واحدة فورية"""
    global _reader
    if _reader is None:
        setup()
    
    try:
        id, text = _reader.read_no_block()
        if id is not None:
            return int(id)
        return None
    except Exception as e:
        print(f"⚠️ RFID read error: {e}")
        return None

def read_tag_stable(stable_reads=3, window_s=0.5):
    """
    قراءة Tag مع التأكد من الاستقرار
    
    Args:
        stable_reads: عدد القراءات المتطابقة المطلوبة
        window_s: النافذة الزمنية للقراءات
    
    Returns:
        int: رقم الـ Tag أو None
    """
    global _reader
    if _reader is None:
        setup()
    
    readings = []
    start_time = time.time()
    
    while time.time() - start_time < window_s:
        try:
            id, text = _reader.read_no_block()
            if id is not None:
                readings.append(int(id))
            time.sleep(0.05)  # فترة قصيرة بين القراءات
        except Exception as e:
            print(f"⚠️ RFID read error: {e}")
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

def read_tag_blocking(timeout=5.0):
    """
    قراءة Tag مع انتظار حتى يتم العثور عليها
    
    Args:
        timeout: الحد الأقصى للانتظار بالثواني
    
    Returns:
        int: رقم الـ Tag أو None
    """
    global _reader
    if _reader is None:
        setup()
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        tag = read_tag_once()
        if tag is not None:
            return tag
        time.sleep(0.1)
    
    return None

def cleanup():
    """تنظيف الموارد"""
    global _reader
    _reader = None
    # لا نقوم بـ GPIO.cleanup() هنا لأنه يتم في الكود الرئيسي