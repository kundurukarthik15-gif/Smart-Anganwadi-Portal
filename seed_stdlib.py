"""
Seed Teacher & Staff centers via Supabase REST API (no Python subprocess needed).
"""
import os, uuid, json, urllib.request, urllib.parse
from datetime import datetime, timezone

SUPABASE_URL = "https://frwtmqkwmtnoibrnytrt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZyd3RtcWt3bXRub2licm55dHJ0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MDY0NDg0OCwiZXhwIjoyMDk2MjIwODQ4fQ.dRaM9C4FF3X0tIqJ8cQSD2UyQxMyE472KMI52FFjK1s"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def uid(): return str(uuid.uuid4())

def insert(table, records):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    data = json.dumps(records).encode()
    req = urllib.request.Request(url, data=data, headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            print(f"  ✅ {table}: inserted {len(records)} records (status {r.status})")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  ⚠️  {table}: {e.code} — {body[:200]}")

TEACHER = "22222222-2222-2222-2222-222222222222"
STAFF   = "33333333-3333-3333-3333-333333333333"

print("Seeding Gandhi Nagar (Teacher) center ...")

insert("children", [
    {"id":uid(),"child_name":"Ramya Reddy",   "age":4,"gender":"Female","parent_name":"Vinod Reddy",  "parent_mobile":"9222111001","center_id":TEACHER},
    {"id":uid(),"child_name":"Suresh Yadav",  "age":5,"gender":"Male",  "parent_name":"Kishore Yadav","parent_mobile":"9222111002","center_id":TEACHER},
    {"id":uid(),"child_name":"Kavitha Nair",  "age":3,"gender":"Female","parent_name":"Arun Nair",    "parent_mobile":"9222111003","center_id":TEACHER},
    {"id":uid(),"child_name":"Nikhil Sharma", "age":6,"gender":"Male",  "parent_name":"Deepak Sharma","parent_mobile":"9222111004","center_id":TEACHER},
    {"id":uid(),"child_name":"Pooja Devi",    "age":4,"gender":"Female","parent_name":"Mahesh Devi",  "parent_mobile":"9222111005","center_id":TEACHER},
    {"id":uid(),"child_name":"Rajan Kumar",   "age":7,"gender":"Male",  "parent_name":"Sanjay Kumar", "parent_mobile":"9222111006","center_id":TEACHER},
])

insert("beneficiaries", [
    {"id":uid(),"name":"Meena Sharma",  "category":"Pregnant Woman",  "mobile":"9222222001","address":"Colony A, Gandhi Nagar","center_id":TEACHER},
    {"id":uid(),"name":"Rekha Devi",    "category":"Lactating Mother","mobile":"9222222002","address":"Street 3, Gandhi Nagar","center_id":TEACHER},
    {"id":uid(),"name":"Sunita Rao",    "category":"Pregnant Woman",  "mobile":"9222222003","address":"Plot 12, Gandhi Nagar", "center_id":TEACHER},
    {"id":uid(),"name":"Kavitha Pillai","category":"Lactating Mother","mobile":"9222222004","address":"Block B, Gandhi Nagar", "center_id":TEACHER},
])

insert("stock_entries", [
    {"id":uid(),"item_name":"Rice (kg)",    "quantity_received":90, "quantity_distributed":15,"remaining_quantity":75,"min_quantity":30,"unit":"kg",     "received_date":"2024-07-01","supplier":"Government Ration","center_id":TEACHER},
    {"id":uid(),"item_name":"Eggs",         "quantity_received":200,"quantity_distributed":40,"remaining_quantity":160,"min_quantity":40,"unit":"units",  "received_date":"2024-07-01","supplier":"Government Supply","center_id":TEACHER},
    {"id":uid(),"item_name":"Milk (Litres)","quantity_received":30, "quantity_distributed":8, "remaining_quantity":22,"min_quantity":15,"unit":"litres", "received_date":"2024-07-02","supplier":"Local Dairy",      "center_id":TEACHER},
    {"id":uid(),"item_name":"Chikki",       "quantity_received":40, "quantity_distributed":20,"remaining_quantity":20,"min_quantity":20,"unit":"packets","received_date":"2024-07-02","supplier":"Health Department","center_id":TEACHER},
])

print("\nSeeding Nehru Colony (Staff) center ...")

insert("children", [
    {"id":uid(),"child_name":"Aditya Singh", "age":5,"gender":"Male",  "parent_name":"Rajesh Singh",  "parent_mobile":"9333111001","center_id":STAFF},
    {"id":uid(),"child_name":"Ananya Joshi", "age":4,"gender":"Female","parent_name":"Pradeep Joshi", "parent_mobile":"9333111002","center_id":STAFF},
    {"id":uid(),"child_name":"Bhavesh Patel","age":6,"gender":"Male",  "parent_name":"Amit Patel",    "parent_mobile":"9333111003","center_id":STAFF},
    {"id":uid(),"child_name":"Deepika Rao",  "age":3,"gender":"Female","parent_name":"Venkat Rao",    "parent_mobile":"9333111004","center_id":STAFF},
    {"id":uid(),"child_name":"Ganesh Babu",  "age":5,"gender":"Male",  "parent_name":"Ravi Babu",     "parent_mobile":"9333111005","center_id":STAFF},
])

insert("beneficiaries", [
    {"id":uid(),"name":"Saradha Bai","category":"Pregnant Woman",  "mobile":"9333222001","address":"Lane 2, Nehru Colony",  "center_id":STAFF},
    {"id":uid(),"name":"Tulasi Devi","category":"Lactating Mother","mobile":"9333222002","address":"Ward 7, Nehru Colony",  "center_id":STAFF},
    {"id":uid(),"name":"Usha Rani",  "category":"Pregnant Woman",  "mobile":"9333222003","address":"Sector 4, Nehru Colony","center_id":STAFF},
])

insert("stock_entries", [
    {"id":uid(),"item_name":"Rice (kg)","quantity_received":70, "quantity_distributed":10,"remaining_quantity":60,"min_quantity":25,"unit":"kg",   "received_date":"2024-07-01","supplier":"Government Ration","center_id":STAFF},
    {"id":uid(),"item_name":"Eggs",     "quantity_received":150,"quantity_distributed":30,"remaining_quantity":120,"min_quantity":30,"unit":"units","received_date":"2024-07-01","supplier":"Government Supply","center_id":STAFF},
    {"id":uid(),"item_name":"Dal (kg)", "quantity_received":25, "quantity_distributed":5, "remaining_quantity":20,"min_quantity":10,"unit":"kg",   "received_date":"2024-07-02","supplier":"Government Supply","center_id":STAFF},
    {"id":uid(),"item_name":"Dates",    "quantity_received":20, "quantity_distributed":8, "remaining_quantity":12,"min_quantity":8, "unit":"kg",   "received_date":"2024-07-02","supplier":"Government Supply","center_id":STAFF},
])

print("\n✅ Done! Each demo account now has its own unique data:")
print("  admin@anganwadi.gov.in (admin@123)   → Rajiv Nagar  → 8 kids, 5 beneficiaries")
print("  teacher@anganwadi.gov.in (teach@123) → Gandhi Nagar → 6 kids, 4 beneficiaries")
print("  staff@anganwadi.gov.in  (staff@123)  → Nehru Colony → 5 kids, 3 beneficiaries")
