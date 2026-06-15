import os
import uuid
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print("=== Supabase Insert Test ===")
supabase: Client = create_client(url, key)

dummy_user_id = str(uuid.uuid4())
dummy_center_id = str(uuid.uuid4())

print(f"Generated User ID: {dummy_user_id}")
print(f"Generated Center ID: {dummy_center_id}")

try:
    # 1. Insert Center
    print("\nInserting test center...")
    center_record = {
        "id": dummy_center_id,
        "center_name": "Test Diagnostic Center",
        "district": "Test District",
        "mandal": "Test Mandal",
        "village": "Test Village",
        "address": "Test Center Address",
        "created_at": "2026-06-15T15:00:00.000Z"
    }
    res_center = supabase.table("centers").insert(center_record).execute()
    print("Success: Center inserted!")
    print(res_center.data)
    
    # 2. Insert User
    print("\nInserting test user...")
    user_record = {
        "id": dummy_user_id,
        "full_name": "Diagnostic Test User",
        "email": f"test_{uuid.uuid4().hex[:6]}@example.com",
        "password_hash": "dummy_hash",
        "center_id": dummy_center_id,
        "created_at": "2026-06-15T15:00:00.000Z",
        "profile_photo": "https://example.com/avatar.png"
    }
    try:
        res_user = supabase.table("users").insert(user_record).execute()
        print("Success: User inserted with profile_photo!")
        print(res_user.data)
    except Exception as e_user_photo:
        print(f"Failed to insert with profile_photo: {e_user_photo}")
        print("Trying insert without profile_photo...")
        user_record.pop("profile_photo", None)
        res_user = supabase.table("users").insert(user_record).execute()
        print("Success: User inserted without profile_photo!")
        print(res_user.data)
        
    # 3. Insert Stock Entries
    print("\nInserting test stock entries...")
    stock_record = {
        "id": str(uuid.uuid4()),
        "item_name": "Test Item",
        "quantity_received": 10.0,
        "quantity_distributed": 0.0,
        "remaining_quantity": 10.0,
        "min_quantity": 5.0,
        "unit": "kg",
        "received_date": "2026-06-15",
        "supplier": "Government Supply",
        "notes": "Initial Seed Stock",
        "center_id": dummy_center_id,
        "created_at": "2026-06-15T15:00:00.000Z"
    }
    res_stock = supabase.table("stock_entries").insert(stock_record).execute()
    print("Success: Stock entries inserted!")
    print(res_stock.data)
    
    # Cleanup test records
    print("\nCleaning up test records...")
    supabase.table("stock_entries").delete().eq("center_id", dummy_center_id).execute()
    supabase.table("users").delete().eq("id", dummy_user_id).execute()
    supabase.table("centers").delete().eq("id", dummy_center_id).execute()
    print("Cleanup completed.")
    
except Exception as e:
    print("\n❌ Insert Test FAILED:")
    import traceback
    traceback.print_exc()
