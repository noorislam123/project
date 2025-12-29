

# rfid_reader.py
import time
from mfrc522 import MFRC522

_reader = MFRC522()

def read_tag(timeout=0.15, poll_delay=0.01):
    end = time.time() + timeout
    while time.time() < end:
        (status, _) = _reader.MFRC522_Request(_reader.PICC_REQIDL)
        if status == _reader.MI_OK:
            (status, uid) = _reader.MFRC522_Anticoll()
            if status == _reader.MI_OK and uid:
                uid_int = (
                    (uid[0] << 32)
                    + (uid[1] << 24)
                    + (uid[2] << 16)
                    + (uid[3] << 8)
                    + uid[4]
                )
                return uid_int
        time.sleep(poll_delay)
    return None


def read_tag_stable(stable_reads=2, window_s=0.5):
    start = time.time()
    last = None
    count = 0

    while time.time() - start < window_s:
        tag = read_tag(timeout=0.08)
        if tag is None:
            continue

        if tag == last:
            count += 1
        else:
            last = tag
            count = 1

        if count >= stable_reads:
            return last

    return None
