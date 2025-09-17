import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load .env file
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# ---------------- Functions ----------------

# 1. CREATE
def add_member(name, email):
    resp = supabase.table("members").insert({"name": name, "email": email}).execute()
    return resp.data

def add_book(title, author, category, stock):
    resp = supabase.table("books").insert(
        {"title": title, "author": author, "category": category, "stock": stock}
    ).execute()
    return resp.data


# 2. READ
def list_books():
    return supabase.table("books").select("*").execute().data

def search_books(keyword):
    return supabase.table("books").select("*").or_(
        f"title.ilike.%{keyword}%,author.ilike.%{keyword}%,category.ilike.%{keyword}%"
    ).execute().data

def member_with_borrowed(member_id):
    return (
        supabase.table("borrow_records")
        .select("record_id, borrow_date, return_date, books(title, author), members(name, email)")
        .eq("member_id", member_id)
        .execute()
        .data
    )


# 3. UPDATE
def update_book_stock(book_id, new_stock):
    return supabase.table("books").update({"stock": new_stock}).eq("book_id", book_id).execute().data

def update_member_email(member_id, new_email):
    return supabase.table("members").update({"email": new_email}).eq("member_id", member_id).execute().data


# 4. DELETE
def delete_member(member_id):
    # only if no borrowed books
    active = supabase.table("borrow_records").select("*").eq("member_id", member_id).is_("return_date", None).execute().data
    if active:
        return {"error": " Member has borrowed books, cannot delete."}
    return supabase.table("members").delete().eq("member_id", member_id).execute().data

def delete_book(book_id):
    active = supabase.table("borrow_records").select("*").eq("book_id", book_id).is_("return_date", None).execute().data
    if active:
        return {"error": " Book is currently borrowed, cannot delete."}
    return supabase.table("books").delete().eq("book_id", book_id).execute().data


# 5. BORROW BOOK (Transaction)
def borrow_book(member_id, book_id):
    # check stock
    book = supabase.table("books").select("*").eq("book_id", book_id).execute().data
    if not book:
        return {"error": " Book not found."}
    if book[0]["stock"] <= 0:
        return {"error": " Book not available."}

    # decrease stock
    supabase.table("books").update({"stock": book[0]["stock"] - 1}).eq("book_id", book_id).execute()
    # insert borrow record
    supabase.table("borrow_records").insert({"member_id": member_id, "book_id": book_id}).execute()
    return {"success": f" Book '{book[0]['title']}' borrowed."}


# 6. RETURN BOOK (Transaction)
def return_book(record_id):
    # get record
    rec = supabase.table("borrow_records").select("*").eq("record_id", record_id).execute().data
    if not rec:
        return {"error": " Record not found."}
    if rec[0]["return_date"]:
        return {"error": " Already returned."}

    book_id = rec[0]["book_id"]

    # update return_date
    supabase.table("borrow_records").update({"return_date": datetime.now().isoformat()}).eq("record_id", record_id).execute()

    # increase stock
    book = supabase.table("books").select("stock").eq("book_id", book_id).execute().data[0]
    supabase.table("books").update({"stock": book["stock"] + 1}).eq("book_id", book_id).execute()

    return {"success": "✅ Book returned successfully."}


# 7. REPORTS
def top_borrowed_books():
    query = """
    SELECT books.title, books.author, COUNT(borrow_records.record_id) AS borrow_count
    FROM borrow_records
    JOIN books ON borrow_records.book_id = books.book_id
    GROUP BY books.title, books.author
    ORDER BY borrow_count DESC
    LIMIT 5;
    """
    return supabase.rpc("exec_sql", {"sql": query}).execute().data

def overdue_books():
    # overdue >14 days and not returned
    cutoff = datetime.now() - timedelta(days=14)
    return (
        supabase.table("borrow_records")
        .select("record_id, borrow_date, members(name, email), books(title)")
        .is_("return_date", None)
        .lt("borrow_date", cutoff.isoformat())
        .execute()
        .data
    )

def books_per_member():
    query = """
    SELECT members.name, members.email, COUNT(borrow_records.record_id) AS total_borrowed
    FROM members
    LEFT JOIN borrow_records ON members.member_id = borrow_records.member_id
    GROUP BY members.name, members.email;
    """
    return supabase.rpc("exec_sql", {"sql": query}).execute().data


# ---------------- Menu ----------------
if __name__ == "__main__":
    while True:
        print("\n Library Management System")
        print("1. Add Member")
        print("2. Add Book")
        print("3. List All Books")
        print("4. Search Books")
        print("5. Show Member & Borrowed Books")
        print("6. Update Book Stock")
        print("7. Update Member Email")
        print("8. Delete Member")
        print("9. Delete Book")
        print("10. Borrow Book")
        print("11. Return Book")
        print("12. Top 5 Borrowed Books")
        print("13. Overdue Books")
        print("14. Borrow Count per Member")
        print("15. Exit")

        choice = input("Enter choice: ").strip()

        if choice == "1":
            name = input("Enter member name: ")
            email = input("Enter member email: ")
            print(add_member(name, email))

        elif choice == "2":
            title = input("Title: ")
            author = input("Author: ")
            category = input("Category: ")
            stock = int(input("Stock: "))
            print(add_book(title, author, category, stock))

        elif choice == "3":
            for b in list_books():
                print(f"{b['book_id']} - {b['title']} by {b['author']} ({b['category']}) Stock: {b['stock']}")

        elif choice == "4":
            keyword = input("Enter keyword: ")
            for b in search_books(keyword):
                print(f"{b['title']} by {b['author']} ({b['category']}) Stock: {b['stock']}")

        elif choice == "5":
            member_id = int(input("Enter Member ID: "))
            recs = member_with_borrowed(member_id)
            if not recs:
                print("No records.")
            else:
                print(f"👤 {recs[0]['members']['name']} ({recs[0]['members']['email']})")
                for r in recs:
                    print(f" - {r['books']['title']} by {r['books']['author']} (Borrowed: {r['borrow_date']}, Returned: {r['return_date']})")

        elif choice == "6":
            book_id = int(input("Book ID: "))
            stock = int(input("New Stock: "))
            print(update_book_stock(book_id, stock))

        elif choice == "7":
            member_id = int(input("Member ID: "))
            new_email = input("New Email: ")
            print(update_member_email(member_id, new_email))

        elif choice == "8":
            member_id = int(input("Member ID: "))
            print(delete_member(member_id))

        elif choice == "9":
            book_id = int(input("Book ID: "))
            print(delete_book(book_id))

        elif choice == "10":
            member_id = int(input("Member ID: "))
            book_id = int(input("Book ID: "))
            print(borrow_book(member_id, book_id))

        elif choice == "11":
            record_id = int(input("Borrow Record ID: "))
            print(return_book(record_id))

        elif choice == "12":
            print(top_borrowed_books())

        elif choice == "13":
            for r in overdue_books():
                print(f"{r['members']['name']} borrowed {r['books']['title']} on {r['borrow_date']} (OVERDUE)")

        elif choice == "14":
            print(books_per_member())

        elif choice == "15":
            print("Exiting...")
            break

        else:
            print(" Invalid choice.")
