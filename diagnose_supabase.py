import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print("=== Supabase Connection Diagnostic ===")
print(f"URL: {url}")
print(f"Key length: {len(key) if key else 0}")

try:
    print("\nConnecting to Supabase...")
    supabase: Client = create_client(url, key)
    print("Success: Client created.")
    
    print("\nQuerying 'centers' table...")
    res = supabase.table("centers").select("*").limit(1).execute()
    print("Success! Data received:")
    print(res.data)
    
    print("\nQuerying 'users' table...")
    res_user = supabase.table("users").select("*").limit(1).execute()
    print("Success! Data received:")
    print(res_user.data)
    
    print("\nQuerying 'stock_entries' table...")
    res_stock = supabase.table("stock_entries").select("*").limit(1).execute()
    print("Success! Data received:")
    print(res_stock.data)
    
except Exception as e:
    print("\n❌ Error occurred during query:")
    import traceback
    traceback.print_exc()
