import csv

barcode_file = "barcode_results.csv"
database_file = "book_database.csv"

# Read barcode results
books = []
with open(barcode_file, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if row["Barcode Data"] not in ["No barcode found", "File not found"]:
            books.append(row)

# Create new book database
with open(database_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Book Folder", "Barcode", "Title", "Author", "Shelf"])

    for book in books:
        print(f"\nBook: {book['Book Folder']} ({book['Barcode Data']})")
        title = input("Enter book title: ")
        author = input("Enter author name: ")
        shelf = input("Enter shelf number: ")

        writer.writerow([book["Book Folder"], book["Barcode Data"], title, author, shelf])
        print("Added successfully!")

print(f"\nDatabase created: {database_file}")
