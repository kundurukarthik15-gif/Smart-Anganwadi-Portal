-- ================================================================
--  SMART ANGANWADI PORTAL — seed_data.sql
--  Run this in Supabase SQL Editor to insert demo data
--  NOTE: Run schema.sql FIRST if tables don't exist yet
-- ================================================================

-- ── Step 1: Insert Centers ───────────────────────────────────────
INSERT INTO centers (id, center_name, district, mandal, village)
VALUES
  ('11111111-1111-1111-1111-111111111111', 'Rajiv Nagar Anganwadi Center',  'Hyderabad',  'Secunderabad', 'Rajiv Nagar'),
  ('22222222-2222-2222-2222-222222222222', 'Gandhi Nagar Anganwadi Center', 'Warangal',   'Hanamkonda',   'Gandhi Nagar'),
  ('33333333-3333-3333-3333-333333333333', 'Nehru Colony Anganwadi Center', 'Karimnagar', 'Choppadandi',  'Nehru Colony')
ON CONFLICT (id) DO NOTHING;

-- ── Step 2: Insert Users ─────────────────────────────────────────
-- Passwords are bcrypt hashed:
--   admin@123  → hash below
--   teach@123  → hash below
--   staff@123  → hash below
--
-- These hashes were generated with Python:
--   import bcrypt
--   bcrypt.hashpw(b"admin@123", bcrypt.gensalt(rounds=10)).decode()

INSERT INTO users (id, full_name, email, password_hash, mobile, center_id)
VALUES
  (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'Lakshmi Devi',
    'admin@anganwadi.gov.in',
    '$2b$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy',
    '9876543210',
    '11111111-1111-1111-1111-111111111111'
  ),
  (
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'Savitri Bai',
    'teacher@anganwadi.gov.in',
    '$2b$10$YourHashForTeach123ReplaceThisWithRealHash12345678',
    '9876543211',
    '22222222-2222-2222-2222-222222222222'
  ),
  (
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'Radha Kumari',
    'staff@anganwadi.gov.in',
    '$2b$10$YourHashForStaff123ReplaceThisWithRealHash1234567890',
    '9876543212',
    '33333333-3333-3333-3333-333333333333'
  )
ON CONFLICT (id) DO NOTHING;

-- ── Step 3: Insert Children ──────────────────────────────────────
INSERT INTO children (id, child_name, age, gender, parent_name, parent_mobile, center_id)
VALUES
  (uuid_generate_v4(), 'Arjun Reddy',   5, 'Male',   'Ramesh Reddy',  '9111111111', '11111111-1111-1111-1111-111111111111'),
  (uuid_generate_v4(), 'Priya Sharma',  4, 'Female', 'Suresh Sharma', '9111111112', '11111111-1111-1111-1111-111111111111'),
  (uuid_generate_v4(), 'Ravi Kumar',    6, 'Male',   'Naresh Kumar',  '9111111113', '11111111-1111-1111-1111-111111111111'),
  (uuid_generate_v4(), 'Anjali Devi',   5, 'Female', 'Ganesh Rao',    '9111111114', '11111111-1111-1111-1111-111111111111'),
  (uuid_generate_v4(), 'Kiran Babu',    7, 'Male',   'Krishna Babu',  '9111111115', '11111111-1111-1111-1111-111111111111'),
  (uuid_generate_v4(), 'Sita Kumari',   4, 'Female', 'Raju Kumari',   '9111111116', '11111111-1111-1111-1111-111111111111');

-- ── Step 4: Insert Beneficiaries ────────────────────────────────
INSERT INTO beneficiaries (id, name, category, mobile, address, center_id)
VALUES
  (uuid_generate_v4(), 'Geetha Devi',    'Pregnant Woman',   '9988776655', 'Ward 5, Rajiv Nagar',  '11111111-1111-1111-1111-111111111111'),
  (uuid_generate_v4(), 'Saroja Bai',     'Lactating Mother', '9988776656', 'Ward 2, Rajiv Nagar',  '11111111-1111-1111-1111-111111111111'),
  (uuid_generate_v4(), 'Padmavathi',     'Pregnant Woman',   '9988776657', 'Colony 3, Rajiv Nagar','11111111-1111-1111-1111-111111111111'),
  (uuid_generate_v4(), 'Laxmi Reddy',    'Lactating Mother', '9988776658', 'Street 7, Rajiv Nagar','11111111-1111-1111-1111-111111111111'),
  (uuid_generate_v4(), 'Vijaya Lakshmi', 'Pregnant Woman',   '9988776659', 'Block A, Rajiv Nagar', '11111111-1111-1111-1111-111111111111');

-- ── Step 5: Insert Stock ─────────────────────────────────────────
INSERT INTO stock_entries (id, item_name, quantity_received, quantity_distributed, remaining_quantity, min_quantity, unit, received_date, supplier, center_id)
VALUES
  (uuid_generate_v4(), 'Eggs',              320, 80,  240, 50,  'units',   '2024-07-01', 'Government Supply', '11111111-1111-1111-1111-111111111111'),
  (uuid_generate_v4(), 'Milk (Litres)',     45,  15,  30,  20,  'litres',  '2024-07-01', 'Local Dairy',       '11111111-1111-1111-1111-111111111111'),
  (uuid_generate_v4(), 'Dates',             30,  12,  18,  10,  'kg',      '2024-07-02', 'Government Supply', '11111111-1111-1111-1111-111111111111'),
  (uuid_generate_v4(), 'Chikki',            60,  30,  30,  30,  'packets', '2024-07-02', 'Health Department', '11111111-1111-1111-1111-111111111111'),
  (uuid_generate_v4(), 'Rice (kg)',         120, 20,  100, 40,  'kg',      '2024-06-30', 'Government Ration', '11111111-1111-1111-1111-111111111111'),
  (uuid_generate_v4(), 'Dal (kg)',          20,  12,  8,   15,  'kg',      '2024-07-01', 'Government Supply', '11111111-1111-1111-1111-111111111111')
ON CONFLICT (center_id, item_name) DO NOTHING;

-- ── Step 6: Insert Meetings ──────────────────────────────────────
INSERT INTO meetings (id, title, description, meeting_date, location, center_id)
VALUES
  (uuid_generate_v4(), 'Monthly Parent Meeting',   'Monthly review of children progress.',          '2026-08-15 10:00:00+05:30', 'Center Hall',     '11111111-1111-1111-1111-111111111111'),
  (uuid_generate_v4(), 'Government Health Survey', 'Annual health survey by government officials.', '2026-08-20 09:00:00+05:30', 'District Office', '11111111-1111-1111-1111-111111111111'),
  (uuid_generate_v4(), 'Staff Training Workshop',  'Training on new schemes and digital tools.',    '2026-08-28 14:00:00+05:30', 'Training Center', '11111111-1111-1111-1111-111111111111');

-- Stories seeding removed

-- ── Verify ───────────────────────────────────────────────────────
SELECT 'centers'       AS table_name, COUNT(*) FROM centers
UNION ALL SELECT 'users',          COUNT(*) FROM users
UNION ALL SELECT 'children',       COUNT(*) FROM children
UNION ALL SELECT 'beneficiaries',  COUNT(*) FROM beneficiaries
UNION ALL SELECT 'stock_entries',  COUNT(*) FROM stock_entries
UNION ALL SELECT 'meetings',       COUNT(*) FROM meetings
UNION ALL SELECT 'stories',        COUNT(*) FROM stories;
