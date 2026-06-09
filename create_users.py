# ================================================================
#  create_users.py
#  Run this ONCE to create demo users in Supabase
#  Usage: python create_users.py
# ================================================================

import os
import uuid
import bcrypt
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://frwtmqkwmtnoibrnytrt.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZyd3RtcWt3bXRub2licm55dHJ0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA2NDQ4NDgsImV4cCI6MjA5NjIyMDg0OH0.gxC3rbSIG2Dmb-u5cQWHWiqhcajK0G2EbETcRrRq8Ag")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def hash_pw(plain):
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=10)).decode()

# ── Centers ──────────────────────────────────────────────────────
centers = [
    {"id": "11111111-1111-1111-1111-111111111111", "center_name": "Rajiv Nagar Anganwadi Center",  "district": "Hyderabad",  "mandal": "Secunderabad", "village": "Rajiv Nagar"},
    {"id": "22222222-2222-2222-2222-222222222222", "center_name": "Gandhi Nagar Anganwadi Center", "district": "Warangal",   "mandal": "Hanamkonda",   "village": "Gandhi Nagar"},
    {"id": "33333333-3333-3333-3333-333333333333", "center_name": "Nehru Colony Anganwadi Center", "district": "Karimnagar", "mandal": "Choppadandi",  "village": "Nehru Colony"},
]

# ── Users ─────────────────────────────────────────────────────────
users = [
    {"id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "full_name": "Lakshmi Devi", "email": "admin@anganwadi.gov.in",   "password": "admin@123", "mobile": "9876543210", "center_id": "11111111-1111-1111-1111-111111111111"},
    {"id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "full_name": "Savitri Bai",  "email": "teacher@anganwadi.gov.in","password": "teach@123", "mobile": "9876543211", "center_id": "22222222-2222-2222-2222-222222222222"},
    {"id": "cccccccc-cccc-cccc-cccc-cccccccccccc", "full_name": "Radha Kumari", "email": "staff@anganwadi.gov.in",  "password": "staff@123", "mobile": "9876543212", "center_id": "33333333-3333-3333-3333-333333333333"},
]

# ── Children ──────────────────────────────────────────────────────
children = [
    {"child_name": "Arjun Reddy",   "age": 5, "gender": "Male",   "parent_name": "Ramesh Reddy",  "parent_mobile": "9111111111", "center_id": "11111111-1111-1111-1111-111111111111"},
    {"child_name": "Priya Sharma",  "age": 4, "gender": "Female", "parent_name": "Suresh Sharma", "parent_mobile": "9111111112", "center_id": "11111111-1111-1111-1111-111111111111"},
    {"child_name": "Ravi Kumar",    "age": 6, "gender": "Male",   "parent_name": "Naresh Kumar",  "parent_mobile": "9111111113", "center_id": "11111111-1111-1111-1111-111111111111"},
    {"child_name": "Anjali Devi",   "age": 5, "gender": "Female", "parent_name": "Ganesh Rao",    "parent_mobile": "9111111114", "center_id": "11111111-1111-1111-1111-111111111111"},
    {"child_name": "Kiran Babu",    "age": 7, "gender": "Male",   "parent_name": "Krishna Babu",  "parent_mobile": "9111111115", "center_id": "11111111-1111-1111-1111-111111111111"},
    {"child_name": "Sita Kumari",   "age": 4, "gender": "Female", "parent_name": "Raju Kumari",   "parent_mobile": "9111111116", "center_id": "11111111-1111-1111-1111-111111111111"},
    {"child_name": "Mohan Das",     "age": 3, "gender": "Male",   "parent_name": "Sunil Das",     "parent_mobile": "9111111117", "center_id": "11111111-1111-1111-1111-111111111111"},
    {"child_name": "Durga Bhavani", "age": 6, "gender": "Female", "parent_name": "Prakash Rao",   "parent_mobile": "9111111118", "center_id": "11111111-1111-1111-1111-111111111111"},
]

# ── Beneficiaries ─────────────────────────────────────────────────
beneficiaries = [
    {"name": "Geetha Devi",    "category": "Pregnant Woman",   "mobile": "9988776655", "address": "Ward 5, Rajiv Nagar",   "center_id": "11111111-1111-1111-1111-111111111111"},
    {"name": "Saroja Bai",     "category": "Lactating Mother", "mobile": "9988776656", "address": "Ward 2, Rajiv Nagar",   "center_id": "11111111-1111-1111-1111-111111111111"},
    {"name": "Padmavathi",     "category": "Pregnant Woman",   "mobile": "9988776657", "address": "Colony 3, Rajiv Nagar", "center_id": "11111111-1111-1111-1111-111111111111"},
    {"name": "Laxmi Reddy",    "category": "Lactating Mother", "mobile": "9988776658", "address": "Street 7, Rajiv Nagar", "center_id": "11111111-1111-1111-1111-111111111111"},
    {"name": "Vijaya Lakshmi", "category": "Pregnant Woman",   "mobile": "9988776659", "address": "Block A, Rajiv Nagar",  "center_id": "11111111-1111-1111-1111-111111111111"},
]

# ── Stock ─────────────────────────────────────────────────────────
stock = [
    {"item_name": "Eggs",          "quantity_received": 320, "quantity_distributed": 80,  "remaining_quantity": 240, "min_quantity": 50,  "unit": "units",   "received_date": "2024-07-01", "supplier": "Government Supply", "center_id": "11111111-1111-1111-1111-111111111111"},
    {"item_name": "Milk (Litres)", "quantity_received": 45,  "quantity_distributed": 15,  "remaining_quantity": 30,  "min_quantity": 20,  "unit": "litres",  "received_date": "2024-07-01", "supplier": "Local Dairy",       "center_id": "11111111-1111-1111-1111-111111111111"},
    {"item_name": "Dates",         "quantity_received": 30,  "quantity_distributed": 12,  "remaining_quantity": 18,  "min_quantity": 10,  "unit": "kg",      "received_date": "2024-07-02", "supplier": "Government Supply", "center_id": "11111111-1111-1111-1111-111111111111"},
    {"item_name": "Chikki",        "quantity_received": 60,  "quantity_distributed": 30,  "remaining_quantity": 30,  "min_quantity": 30,  "unit": "packets", "received_date": "2024-07-02", "supplier": "Health Department", "center_id": "11111111-1111-1111-1111-111111111111"},
    {"item_name": "Rice (kg)",     "quantity_received": 120, "quantity_distributed": 20,  "remaining_quantity": 100, "min_quantity": 40,  "unit": "kg",      "received_date": "2024-06-30", "supplier": "Government Ration", "center_id": "11111111-1111-1111-1111-111111111111"},
    {"item_name": "Dal (kg)",      "quantity_received": 20,  "quantity_distributed": 12,  "remaining_quantity": 8,   "min_quantity": 15,  "unit": "kg",      "received_date": "2024-07-01", "supplier": "Government Supply", "center_id": "11111111-1111-1111-1111-111111111111"},
]

# ── Meetings ──────────────────────────────────────────────────────
meetings = [
    {"title": "Monthly Parent Meeting",   "description": "Monthly review of children progress and nutrition status.", "meeting_date": "2026-08-15T10:00:00+05:30", "location": "Center Hall",     "center_id": "11111111-1111-1111-1111-111111111111"},
    {"title": "Government Health Survey", "description": "Annual health survey by government officials.",             "meeting_date": "2026-08-20T09:00:00+05:30", "location": "District Office", "center_id": "11111111-1111-1111-1111-111111111111"},
    {"title": "Staff Training Workshop",  "description": "Training on new government schemes and digital tools.",     "meeting_date": "2026-08-28T14:00:00+05:30", "location": "Training Center", "center_id": "11111111-1111-1111-1111-111111111111"},
]

# ── Stories ───────────────────────────────────────────────────────
stories = []

# ================================================================
#  INSERT ALL DATA
# ================================================================

def insert(table, rows, label):
    try:
        res = supabase.table(table).upsert(rows).execute()
        print(f"  ✅ {label}: {len(rows)} records inserted")
        return True
    except Exception as e:
        print(f"  ❌ {label} failed: {e}")
        return False

print("\n🚀 Smart Anganwadi Portal — Seeding Database")
print("=" * 50)

# Centers
print("\n📍 Inserting Centers...")
insert("centers", centers, "Centers")

# Users (hash passwords)
print("\n👤 Inserting Users (hashing passwords)...")
user_records = []
for u in users:
    print(f"  🔐 Hashing password for {u['email']}...")
    record = {
        "id":            u["id"],
        "full_name":     u["full_name"],
        "email":         u["email"],
        "password_hash": hash_pw(u["password"]),
        "mobile":        u["mobile"],
        "center_id":     u["center_id"],
    }
    user_records.append(record)
    print(f"  ✅ {u['email']} → hash generated")

insert("users", user_records, "Users")

# Children
print("\n👶 Inserting Children...")
child_records = [{**c, "id": str(uuid.uuid4())} for c in children]
insert("children", child_records, "Children")

# Beneficiaries
print("\n🤱 Inserting Beneficiaries...")
benef_records = [{**b, "id": str(uuid.uuid4())} for b in beneficiaries]
insert("beneficiaries", benef_records, "Beneficiaries")

# Stock
print("\n📦 Inserting Stock...")
stock_records = [{**s, "id": str(uuid.uuid4())} for s in stock]
insert("stock_entries", stock_records, "Stock")

# Meetings
print("\n📅 Inserting Meetings...")
meeting_records = [{**m, "id": str(uuid.uuid4())} for m in meetings]
insert("meetings", meeting_records, "Meetings")

# Stories
# Seeding of demo stories removed as requested

print("\n" + "=" * 50)
print("✅ Seeding Complete!")
print("\n🔑 Demo Login Credentials:")
print("   admin@anganwadi.gov.in   → admin@123")
print("   teacher@anganwadi.gov.in → teach@123")
print("   staff@anganwadi.gov.in   → staff@123")
print("\n🌐 Now run: python app.py")
print("=" * 50 + "\n")
