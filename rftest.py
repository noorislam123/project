import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import signal
import time

# إنشاء القارئ
reader = SimpleMFRC522()

# دالة لإيقاف البرنامج عند Ctrl+C
def end_read(signal, frame):
    print("\n🛑 Stopping RFID reader...")
    GPIO.cleanup()
    exit()

signal.signal(signal.SIGINT, end_read)

print("📡 Bring your RFID tag close to the reader...")

try:
    while True:
        id, text = reader.read()
        print(f"✅ Tag detected!\nID: {id}\nData: {text}")
        print("------------------------------")
        time.sleep(2)

except KeyboardInterrupt:
    GPIO.cleanup()
    print("\nProgram stopped")     