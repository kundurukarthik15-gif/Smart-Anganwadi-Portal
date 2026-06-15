import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://frwtmqkwmtnoibrnytrt.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_KEY:
    print("❌ SUPABASE_KEY not found in environment. Please check your .env file.")
    exit(1)

print("🔗 Connecting to Supabase...")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    print("🗑️  Deleting all existing stories from database...")
    # Delete all records by checking if ID is not null (guaranteed for UUID primary keys)
    res = supabase.table("stories").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    count = len(res.data) if res.data else 0
    print(f"✅ Success! Deleted {count} stories from database.")
except Exception as e:
    print(f"❌ Error deleting stories: {e}")
