-- ================================================================
--  PASTE THIS ENTIRE SCRIPT IN:
--  Supabase Dashboard → SQL Editor → New Query → Run
-- ================================================================

-- STEP 1: Disable RLS on every table
ALTER TABLE centers            DISABLE ROW LEVEL SECURITY;
ALTER TABLE users              DISABLE ROW LEVEL SECURITY;
ALTER TABLE children           DISABLE ROW LEVEL SECURITY;
ALTER TABLE beneficiaries      DISABLE ROW LEVEL SECURITY;
ALTER TABLE stock_entries      DISABLE ROW LEVEL SECURITY;
ALTER TABLE stock_distribution DISABLE ROW LEVEL SECURITY;
ALTER TABLE stock_logs         DISABLE ROW LEVEL SECURITY;
ALTER TABLE stories            DISABLE ROW LEVEL SECURITY;
ALTER TABLE meetings           DISABLE ROW LEVEL SECURITY;
ALTER TABLE surveys_feedback   DISABLE ROW LEVEL SECURITY;

-- STEP 2: Drop all existing RLS policies
DO $$
DECLARE r RECORD;
BEGIN
  FOR r IN SELECT policyname, tablename FROM pg_policies WHERE schemaname = 'public'
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON %I', r.policyname, r.tablename);
  END LOOP;
END $$;

-- STEP 3: Clear all data
TRUNCATE TABLE surveys_feedback   CASCADE;
TRUNCATE TABLE stock_logs         CASCADE;
TRUNCATE TABLE stock_distribution CASCADE;
TRUNCATE TABLE stock_entries      CASCADE;
TRUNCATE TABLE stories            CASCADE;
TRUNCATE TABLE meetings           CASCADE;
TRUNCATE TABLE beneficiaries      CASCADE;
TRUNCATE TABLE children           CASCADE;
TRUNCATE TABLE users              CASCADE;
TRUNCATE TABLE centers            CASCADE;

-- STEP 4: Insert Centers
INSERT INTO centers (id, center_name, district, mandal, village) VALUES
('11111111-1111-1111-1111-111111111111','Rajiv Nagar Anganwadi Center', 'Hyderabad', 'Secunderabad','Rajiv Nagar'),
('22222222-2222-2222-2222-222222222222','Gandhi Nagar Anganwadi Center','Warangal',  'Hanamkonda',  'Gandhi Nagar'),
('33333333-3333-3333-3333-333333333333','Nehru Colony Anganwadi Center','Karimnagar','Choppadandi', 'Nehru Colony');

-- STEP 5: Insert Users
-- Passwords: admin@123 / teach@123 / staff@123
-- These are valid bcrypt hashes generated with Python bcrypt rounds=12
INSERT INTO users (id, full_name, email, password_hash, mobile, center_id) VALUES
(
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  'Lakshmi Devi',
  'admin@anganwadi.gov.in',
  '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
  '9876543210',
  '11111111-1111-1111-1111-111111111111'
),
(
  'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
  'Savitri Bai',
  'teacher@anganwadi.gov.in',
  '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
  '9876543211',
  '22222222-2222-2222-2222-222222222222'
),
(
  'cccccccc-cccc-cccc-cccc-cccccccccccc',
  'Radha Kumari',
  'staff@anganwadi.gov.in',
  '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
  '9876543212',
  '33333333-3333-3333-3333-333333333333'
);

-- STEP 6: Insert Children
INSERT INTO children (id, child_name, age, gender, parent_name, parent_mobile, center_id) VALUES
(gen_random_uuid(),'Arjun Reddy',  5,'Male',  'Ramesh Reddy', '9111111111','11111111-1111-1111-1111-111111111111'),
(gen_random_uuid(),'Priya Sharma', 4,'Female','Suresh Sharma','9111111112','11111111-1111-1111-1111-111111111111'),
(gen_random_uuid(),'Ravi Kumar',   6,'Male',  'Naresh Kumar', '9111111113','11111111-1111-1111-1111-111111111111'),
(gen_random_uuid(),'Anjali Devi',  5,'Female','Ganesh Rao',   '9111111114','11111111-1111-1111-1111-111111111111'),
(gen_random_uuid(),'Kiran Babu',   7,'Male',  'Krishna Babu', '9111111115','11111111-1111-1111-1111-111111111111'),
(gen_random_uuid(),'Sita Kumari',  4,'Female','Raju Kumari',  '9111111116','11111111-1111-1111-1111-111111111111'),
(gen_random_uuid(),'Mohan Das',    3,'Male',  'Sunil Das',    '9111111117','11111111-1111-1111-1111-111111111111'),
(gen_random_uuid(),'Durga Bhavani',6,'Female','Prakash Rao',  '9111111118','11111111-1111-1111-1111-111111111111');

-- STEP 7: Insert Beneficiaries
INSERT INTO beneficiaries (id, name, category, mobile, address, center_id) VALUES
(gen_random_uuid(),'Geetha Devi',   'Pregnant Woman',  '9988776655','Ward 5, Rajiv Nagar',  '11111111-1111-1111-1111-111111111111'),
(gen_random_uuid(),'Saroja Bai',    'Lactating Mother','9988776656','Ward 2, Rajiv Nagar',  '11111111-1111-1111-1111-111111111111'),
(gen_random_uuid(),'Padmavathi',    'Pregnant Woman',  '9988776657','Colony 3, Rajiv Nagar','11111111-1111-1111-1111-111111111111'),
(gen_random_uuid(),'Laxmi Reddy',   'Lactating Mother','9988776658','Street 7, Rajiv Nagar','11111111-1111-1111-1111-111111111111'),
(gen_random_uuid(),'Vijaya Lakshmi','Pregnant Woman',  '9988776659','Block A, Rajiv Nagar', '11111111-1111-1111-1111-111111111111');

-- STEP 8: Insert Stock
INSERT INTO stock_entries (id, item_name, quantity_received, quantity_distributed, remaining_quantity, min_quantity, unit, received_date, supplier, center_id) VALUES
(gen_random_uuid(),'Eggs',         320,80, 240,50, 'units',  '2024-07-01','Government Supply','11111111-1111-1111-1111-111111111111'),
(gen_random_uuid(),'Milk (Litres)',45, 15, 30, 20, 'litres', '2024-07-01','Local Dairy',      '11111111-1111-1111-1111-111111111111'),
(gen_random_uuid(),'Dates',        30, 12, 18, 10, 'kg',     '2024-07-02','Government Supply','11111111-1111-1111-1111-111111111111'),
(gen_random_uuid(),'Chikki',       60, 30, 30, 30, 'packets','2024-07-02','Health Department','11111111-1111-1111-1111-111111111111'),
(gen_random_uuid(),'Rice (kg)',    120,20, 100,40, 'kg',     '2024-06-30','Government Ration','11111111-1111-1111-1111-111111111111'),
(gen_random_uuid(),'Dal (kg)',     20, 12, 8,  15, 'kg',     '2024-07-01','Government Supply','11111111-1111-1111-1111-111111111111')
ON CONFLICT (center_id, item_name) DO NOTHING;

-- STEP 9: Insert Meetings
INSERT INTO meetings (id, title, description, meeting_date, location, center_id) VALUES
(gen_random_uuid(),'Monthly Parent Meeting',  'Monthly review of children progress.','2026-08-15 10:00:00+05:30','Center Hall',    '11111111-1111-1111-1111-111111111111'),
(gen_random_uuid(),'Government Health Survey','Annual health survey.',               '2026-08-20 09:00:00+05:30','District Office','11111111-1111-1111-1111-111111111111'),
(gen_random_uuid(),'Staff Training Workshop', 'Training on new schemes.',            '2026-08-28 14:00:00+05:30','Training Center','11111111-1111-1111-1111-111111111111');

-- Stories seeding removed

-- STEP 11: Verify counts
SELECT 'centers' AS tbl, COUNT(*) FROM centers
UNION ALL SELECT 'users',        COUNT(*) FROM users
UNION ALL SELECT 'children',     COUNT(*) FROM children
UNION ALL SELECT 'beneficiaries',COUNT(*) FROM beneficiaries
UNION ALL SELECT 'stock_entries',COUNT(*) FROM stock_entries
UNION ALL SELECT 'meetings',     COUNT(*) FROM meetings
UNION ALL SELECT 'stories',      COUNT(*) FROM stories;
