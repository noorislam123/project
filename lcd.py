from RPLCD.i2c import CharLCD
import time

# غيري العنوان إذا لزم (غالباً 0x27 أو 0x3F)
I2C_ADDRESS = 0x27

# تعريف الشاشة: 16x2
lcd = CharLCD(
    i2c_expander='PCF8574',
    address=I2C_ADDRESS,
    port=1,
    cols=16,
    rows=2,
    charmap='A02',
    auto_linebreaks=True
)

try:
    lcd.clear()

    lcd.cursor_pos = (0, 1)
    lcd.write_string("Book shelfed !")

    print("LCD should display text now.")

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Exiting...")
finally:
    lcd.clear()
