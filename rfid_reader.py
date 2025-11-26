import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time

reader = SimpleMFRC522()

def read_tag():
    try:
        id, text = reader.read()   # read once only
        return id                  # return UID as int
    except:
        return None
