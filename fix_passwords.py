# fix_passwords.py — Run after fix_rls_and_seed.sql
# Usage: python fix_passwords.py

import os, bcrypt
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

accounts = [
    ("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "admin@anganwadi.gov.in",   "admin@123"),
    ("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "teacher@anganwadi.gov.in", "teach@123"),
    ("cccccccc-cccc-cccc-cccc-cccccccccccc", "staff@anganwadi.gov.in",   "staff@123"),
]

print("\n🔐 Setting correct password hashes...\n")
for uid, email, pw in accounts:
    h = bcrypt.hashpw(pw.encode(), bcrypt.gensalt(12)).decode()
    supabase.table("users").update({"password_hash": h}).eq("id", uid).execute()
    # verify
    row = supabase.table("users").select("password_hash").eq("id", uid).execute().data
    ok  = row and bcrypt.checkpw(pw.encode(), row[0]["password_hash"].encode())
    print(f"  {'✅' if ok else '❌'} {email} → {'OK' if ok else 'FAILED'}")

print("\n✅ Done! Login with:")
print("   admin@anganwadi.gov.in   / admin@123")
print("   teacher@anganwadi.gov.in / teach@123")
print("   staff@anganwadi.gov.in   / staff@123\n")
