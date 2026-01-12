from RPLCD.i2c import CharLCD
import time

I2C_ADDRESS = 0x27  # غيّري إذا جهازك مختلف

lcd = CharLCD(
    i2c_expander='PCF8574',
    address=I2C_ADDRESS,
    port=1,
    cols=16,
    rows=2,
    charmap='A02',
    auto_linebreaks=True
)

# تضمني الشاشة نظيفة قبل أي طباعة
lcd.clear()
