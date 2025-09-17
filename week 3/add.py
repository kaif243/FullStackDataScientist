import os
from supabase import create_client, Client  # pip install supabase
from dotenv import load_dotenv  # pip install python-dotenv

load_dotenv()

print("URL:", os.getenv("SUPABASE_URL"))  # <-- debug check
print("KEY:", os.getenv("SUPABASE_KEY")[:10])  # only first 10 chars

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb: Client = create_client(url, key)

def add_product(prod_id, name, price, stock):
    payload = {
        "prod_id": prod_id,
        "name": name,
        "price": price,
        "stock": stock
    }
    resp = sb.table("products").insert(payload).execute()
    return resp.data

if __name__ == "__main__":
    prod_id = int(input("Enter product ID: ").strip())   # PK must be unique
    name = input("Enter product name: ").strip()
    price = int(input("Enter price: ").strip())         # table has integer type
    stock = int(input("Enter stock: ").strip())

    created = add_product(prod_id, name, price, stock)
    print("Inserted:", created)
