# ================================================================
#  debug_login.py — Run this to diagnose the login issue
#  Usage: python debug_login.py
# ================================================================

import os
import bcrypt
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://frwtmqkwmtnoibrnytrt.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZyd3RtcWt3bXRub2licm55dHJ0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA2NDQ4NDgsImV4cCI6MjA5NjIyMDg0OH0.gxC3rbSIG2Dmb-u5cQWHWiqhcajK0G2EbETcRrRq8Ag")

print("\n" + "="*60)
print("  SMART ANGANWADI — Login Debug Tool")
print("="*60)

# ── Step 1: Connect to Supabase ──────────────────────────────────
print("\n[1] Connecting to Supabase...")
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("    ✅ Connected!")
except Exception as e:
    print(f"    ❌ Connection failed: {e}")
    exit(1)

# ── Step 2: Check centers table ──────────────────────────────────
print("\n[2] Checking centers table...")
try:
    res = supabase.table("centers").select("*").execute()
    if res.data:
        print(f"    ✅ Found {len(res.data)} center(s)")
        for c in res.data:
            print(f"       - {c['id']} | {c['center_name']}")
    else:
        print("    ⚠️  Centers table is EMPTY — running insert now...")
        supabase.table("centers").insert([
            {"id": "11111111-1111-1111-1111-111111111111", "center_name": "Rajiv Nagar Anganwadi Center",  "district": "Hyderabad",  "mandal": "Secunderabad", "village": "Rajiv Nagar"},
            {"id": "22222222-2222-2222-2222-222222222222", "center_name": "Gandhi Nagar Anganwadi Center", "district": "Warangal",   "mandal": "Hanamkonda",   "village": "Gandhi Nagar"},
            {"id": "33333333-3333-3333-3333-333333333333", "center_name": "Nehru Colony Anganwadi Center", "district": "Karimnagar", "mandal": "Choppadandi",  "village": "Nehru Colony"},
        ]).execute()
        print("    ✅ Centers inserted!")
except Exception as e:
    print(f"    ❌ Centers error: {e}")

# ── Step 3: Check users table ────────────────────────────────────
print("\n[3] Checking users table...")
try:
    res = supabase.table("users").select("id, full_name, email, password_hash, center_id").execute()
    if res.data:
        print(f"    ✅ Found {len(res.data)} user(s)")
        for u in res.data:
            print(f"       - {u['email']} | center: {u['center_id']}")
            print(f"         hash: {u['password_hash'][:30]}...")
    else:
        print("    ⚠️  Users table is EMPTY — inserting users now...")

        # Generate fresh hashes
        users_to_insert = [
            {
                "id":            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "full_name":     "Lakshmi Devi",
                "email":         "admin@anganwadi.gov.in",
                "password_hash": bcrypt.hashpw(b"admin@123", bcrypt.gensalt(10)).decode(),
                "mobile":        "9876543210",
                "center_id":     "11111111-1111-1111-1111-111111111111",
            },
            {
                "id":            "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "full_name":     "Savitri Bai",
                "email":         "teacher@anganwadi.gov.in",
                "password_hash": bcrypt.hashpw(b"teach@123", bcrypt.gensalt(10)).decode(),
                "mobile":        "9876543211",
                "center_id":     "22222222-2222-2222-2222-222222222222",
            },
            {
                "id":            "cccccccc-cccc-cccc-cccc-cccccccccccc",
                "full_name":     "Radha Kumari",
                "email":         "staff@anganwadi.gov.in",
                "password_hash": bcrypt.hashpw(b"staff@123", bcrypt.gensalt(10)).decode(),
                "mobile":        "9876543212",
                "center_id":     "33333333-3333-3333-3333-333333333333",
            },
        ]

        for u in users_to_insert:
            print(f"    🔐 Inserting {u['email']}...")
            supabase.table("users").insert(u).execute()
            print(f"    ✅ Done")

except Exception as e:
    print(f"    ❌ Users error: {e}")

# ── Step 4: Test bcrypt match ────────────────────────────────────
print("\n[4] Testing password hash for admin@anganwadi.gov.in ...")
try:
    res = supabase.table("users").select("email, password_hash").eq("email", "admin@anganwadi.gov.in").execute()
    if not res.data:
        print("    ❌ User still not found in DB!")
    else:
        user = res.data[0]
        stored_hash = user["password_hash"]
        test_pass   = b"admin@123"
        match = bcrypt.checkpw(test_pass, stored_hash.encode())
        print(f"    Email:  {user['email']}")
        print(f"    Hash:   {stored_hash[:40]}...")
        print(f"    Match:  {'✅ PASSWORD MATCHES' if match else '❌ PASSWORD DOES NOT MATCH'}")
except Exception as e:
    print(f"    ❌ Test failed: {e}")

# ── Step 5: Test full login query ────────────────────────────────
print("\n[5] Testing full login query (with centers join)...")
try:
    res = supabase.table("users") \
        .select("*, centers(id, center_name, district, mandal, village)") \
        .eq("email", "admin@anganwadi.gov.in") \
        .execute()
    if res.data:
        u = res.data[0]
        print(f"    ✅ User found: {u['full_name']}")
        print(f"    Center: {u.get('centers', {})}")
    else:
        print("    ❌ No user returned from join query")
except Exception as e:
    print(f"    ❌ Join query failed: {e}")

print("\n" + "="*60)
print("  Debug complete. Check results above.")
print("="*60 + "\n")
