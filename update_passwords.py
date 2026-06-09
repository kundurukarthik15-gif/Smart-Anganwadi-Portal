# ================================================================
#  update_passwords.py
#  Run AFTER fix_rls_and_seed.sql to set correct password hashes
#  Usage: python update_passwords.py
# ================================================================

import os, bcrypt
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://frwtmqkwmtnoibrnytrt.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZyd3RtcWt3bXRub2licm55dHJ0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA2NDQ4NDgsImV4cCI6MjA5NjIyMDg0OH0.gxC3rbSIG2Dmb-u5cQWHWiqhcajK0G2EbETcRrRq8Ag")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

accounts = [
    ("admin@anganwadi.gov.in",   "admin@123"),
    ("teacher@anganwadi.gov.in", "teach@123"),
    ("staff@anganwadi.gov.in",   "staff@123"),
]

print("\n🔐 Updating password hashes...\n")

all_ok = True
for email, password in accounts:
    try:
        new_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(10)).decode()
        res = supabase.table("users").update({"password_hash": new_hash}).eq("email", email).execute()
        if res.data:
            # Verify it works
            stored = res.data[0]["password_hash"]
            ok = bcrypt.checkpw(password.encode(), stored.encode())
            print(f"  {'✅' if ok else '❌'} {email} → {'hash verified' if ok else 'HASH MISMATCH'}")
        else:
            print(f"  ⚠️  {email} → user not found in DB")
            all_ok = False
    except Exception as e:
        print(f"  ❌ {email} → ERROR: {e}")
        all_ok = False

print()
if all_ok:
    print("✅ All passwords updated! You can now login with:")
    print("   admin@anganwadi.gov.in   / admin@123")
    print("   teacher@anganwadi.gov.in / teach@123")
    print("   staff@anganwadi.gov.in   / staff@123")
else:
    print("⚠️  Some updates failed. Make sure fix_rls_and_seed.sql was run first.")
print()
