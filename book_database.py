import csv

DB_FILE = "book_database.csv"

def load_database():
    db = {}
    with open(DB_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            book_folder = row["Book Folder"].strip()
            db[book_folder] = {
                "barcode": row["Barcode"].strip(),
                "title": row["Title"].strip(),
                "author": row["Author"].strip(),
                "shelf": int(row["Shelf"].strip()),
                "rfid": int(row["RFID_Tag"].strip())
            }
    return db


def get_book_info(book_folder):
    db = load_database()
    if book_folder in db:
        return db[book_folder]    # returns dict
    return None
