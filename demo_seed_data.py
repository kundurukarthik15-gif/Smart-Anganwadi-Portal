"""
One-shot seeder endpoint. Mount it in app.py temporarily, call it once,
then remove it. Accessible at POST /api/dev/seed-demo
"""

TEACHER = "22222222-2222-2222-2222-222222222222"
STAFF   = "33333333-3333-3333-3333-333333333333"
import uuid as _uuid

def _uid(): return str(_uuid.uuid4())

TEACHER_CHILDREN = [
    {"id":_uid(),"child_name":"Ramya Reddy",   "age":4,"gender":"Female","parent_name":"Vinod Reddy",  "parent_mobile":"9222111001","center_id":TEACHER},
    {"id":_uid(),"child_name":"Suresh Yadav",  "age":5,"gender":"Male",  "parent_name":"Kishore Yadav","parent_mobile":"9222111002","center_id":TEACHER},
    {"id":_uid(),"child_name":"Kavitha Nair",  "age":3,"gender":"Female","parent_name":"Arun Nair",    "parent_mobile":"9222111003","center_id":TEACHER},
    {"id":_uid(),"child_name":"Nikhil Sharma", "age":6,"gender":"Male",  "parent_name":"Deepak Sharma","parent_mobile":"9222111004","center_id":TEACHER},
    {"id":_uid(),"child_name":"Pooja Devi",    "age":4,"gender":"Female","parent_name":"Mahesh Devi",  "parent_mobile":"9222111005","center_id":TEACHER},
    {"id":_uid(),"child_name":"Rajan Kumar",   "age":7,"gender":"Male",  "parent_name":"Sanjay Kumar", "parent_mobile":"9222111006","center_id":TEACHER},
]
TEACHER_BENEFS = [
    {"id":_uid(),"name":"Meena Sharma",  "category":"Pregnant Woman",  "mobile":"9222222001","address":"Colony A, Gandhi Nagar","center_id":TEACHER},
    {"id":_uid(),"name":"Rekha Devi",    "category":"Lactating Mother","mobile":"9222222002","address":"Street 3, Gandhi Nagar","center_id":TEACHER},
    {"id":_uid(),"name":"Sunita Rao",    "category":"Pregnant Woman",  "mobile":"9222222003","address":"Plot 12, Gandhi Nagar", "center_id":TEACHER},
    {"id":_uid(),"name":"Kavitha Pillai","category":"Lactating Mother","mobile":"9222222004","address":"Block B, Gandhi Nagar", "center_id":TEACHER},
]
TEACHER_STOCK = [
    {"id":_uid(),"item_name":"Rice (kg)",    "quantity_received":90, "quantity_distributed":15,"remaining_quantity":75, "min_quantity":30,"unit":"kg",     "received_date":"2024-07-01","supplier":"Government Ration","center_id":TEACHER},
    {"id":_uid(),"item_name":"Eggs",         "quantity_received":200,"quantity_distributed":40,"remaining_quantity":160,"min_quantity":40,"unit":"units",  "received_date":"2024-07-01","supplier":"Government Supply","center_id":TEACHER},
    {"id":_uid(),"item_name":"Milk (Litres)","quantity_received":30, "quantity_distributed":8, "remaining_quantity":22, "min_quantity":15,"unit":"litres", "received_date":"2024-07-02","supplier":"Local Dairy",      "center_id":TEACHER},
    {"id":_uid(),"item_name":"Chikki",       "quantity_received":40, "quantity_distributed":20,"remaining_quantity":20, "min_quantity":20,"unit":"packets","received_date":"2024-07-02","supplier":"Health Department","center_id":TEACHER},
]
STAFF_CHILDREN = [
    {"id":_uid(),"child_name":"Aditya Singh", "age":5,"gender":"Male",  "parent_name":"Rajesh Singh",  "parent_mobile":"9333111001","center_id":STAFF},
    {"id":_uid(),"child_name":"Ananya Joshi", "age":4,"gender":"Female","parent_name":"Pradeep Joshi", "parent_mobile":"9333111002","center_id":STAFF},
    {"id":_uid(),"child_name":"Bhavesh Patel","age":6,"gender":"Male",  "parent_name":"Amit Patel",    "parent_mobile":"9333111003","center_id":STAFF},
    {"id":_uid(),"child_name":"Deepika Rao",  "age":3,"gender":"Female","parent_name":"Venkat Rao",    "parent_mobile":"9333111004","center_id":STAFF},
    {"id":_uid(),"child_name":"Ganesh Babu",  "age":5,"gender":"Male",  "parent_name":"Ravi Babu",     "parent_mobile":"9333111005","center_id":STAFF},
]
STAFF_BENEFS = [
    {"id":_uid(),"name":"Saradha Bai","category":"Pregnant Woman",  "mobile":"9333222001","address":"Lane 2, Nehru Colony",   "center_id":STAFF},
    {"id":_uid(),"name":"Tulasi Devi","category":"Lactating Mother","mobile":"9333222002","address":"Ward 7, Nehru Colony",   "center_id":STAFF},
    {"id":_uid(),"name":"Usha Rani",  "category":"Pregnant Woman",  "mobile":"9333222003","address":"Sector 4, Nehru Colony","center_id":STAFF},
]
STAFF_STOCK = [
    {"id":_uid(),"item_name":"Rice (kg)","quantity_received":70, "quantity_distributed":10,"remaining_quantity":60, "min_quantity":25,"unit":"kg",   "received_date":"2024-07-01","supplier":"Government Ration","center_id":STAFF},
    {"id":_uid(),"item_name":"Eggs",     "quantity_received":150,"quantity_distributed":30,"remaining_quantity":120,"min_quantity":30,"unit":"units","received_date":"2024-07-01","supplier":"Government Supply","center_id":STAFF},
    {"id":_uid(),"item_name":"Dal (kg)", "quantity_received":25, "quantity_distributed":5, "remaining_quantity":20, "min_quantity":10,"unit":"kg",   "received_date":"2024-07-02","supplier":"Government Supply","center_id":STAFF},
    {"id":_uid(),"item_name":"Dates",    "quantity_received":20, "quantity_distributed":8, "remaining_quantity":12, "min_quantity":8, "unit":"kg",   "received_date":"2024-07-02","supplier":"Government Supply","center_id":STAFF},
]
