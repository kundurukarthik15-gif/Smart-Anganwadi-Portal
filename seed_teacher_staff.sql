-- ================================================================
--  SEED DATA FOR TEACHER & STAFF DEMO ACCOUNTS
--  Run this in Supabase SQL Editor to populate the Teacher and
--  Staff centers with their own isolated children & ladies data.
--  This proves that each user sees ONLY their own center's data.
-- ================================================================

-- ── Gandhi Nagar Center  (Teacher / Savitri Bai) ───────────────────
-- Children
INSERT INTO children (id, child_name, age, gender, parent_name, parent_mobile, center_id) VALUES
(gen_random_uuid(),'Ramya Reddy',    4,'Female','Vinod Reddy',    '9222111001','22222222-2222-2222-2222-222222222222'),
(gen_random_uuid(),'Suresh Yadav',   5,'Male',  'Kishore Yadav',  '9222111002','22222222-2222-2222-2222-222222222222'),
(gen_random_uuid(),'Kavitha Nair',   3,'Female','Arun Nair',       '9222111003','22222222-2222-2222-2222-222222222222'),
(gen_random_uuid(),'Nikhil Sharma',  6,'Male',  'Deepak Sharma',  '9222111004','22222222-2222-2222-2222-222222222222'),
(gen_random_uuid(),'Pooja Devi',     4,'Female','Mahesh Devi',     '9222111005','22222222-2222-2222-2222-222222222222'),
(gen_random_uuid(),'Rajan Kumar',    7,'Male',  'Sanjay Kumar',   '9222111006','22222222-2222-2222-2222-222222222222')
ON CONFLICT DO NOTHING;

-- Beneficiaries
INSERT INTO beneficiaries (id, name, category, mobile, address, center_id) VALUES
(gen_random_uuid(),'Meena Sharma',   'Pregnant Woman',  '9222222001','Colony A, Gandhi Nagar',  '22222222-2222-2222-2222-222222222222'),
(gen_random_uuid(),'Rekha Devi',     'Lactating Mother','9222222002','Street 3, Gandhi Nagar',  '22222222-2222-2222-2222-222222222222'),
(gen_random_uuid(),'Sunita Rao',     'Pregnant Woman',  '9222222003','Plot 12, Gandhi Nagar',   '22222222-2222-2222-2222-222222222222'),
(gen_random_uuid(),'Kavitha Pillai', 'Lactating Mother','9222222004','Block B, Gandhi Nagar',   '22222222-2222-2222-2222-222222222222')
ON CONFLICT DO NOTHING;

-- Stock
INSERT INTO stock_entries (id, item_name, quantity_received, quantity_distributed, remaining_quantity, min_quantity, unit, received_date, supplier, center_id) VALUES
(gen_random_uuid(),'Rice (kg)',     90, 15, 75, 30, 'kg',     '2024-07-01','Government Ration',  '22222222-2222-2222-2222-222222222222'),
(gen_random_uuid(),'Eggs',         200, 40,160, 40, 'units',  '2024-07-01','Government Supply',  '22222222-2222-2222-2222-222222222222'),
(gen_random_uuid(),'Milk (Litres)', 30,  8, 22, 15, 'litres', '2024-07-02','Local Dairy',        '22222222-2222-2222-2222-222222222222'),
(gen_random_uuid(),'Chikki',        40, 20, 20, 20, 'packets','2024-07-02','Health Department',  '22222222-2222-2222-2222-222222222222')
ON CONFLICT (center_id, item_name) DO NOTHING;

-- Meetings
INSERT INTO meetings (id, title, description, meeting_date, location, center_id) VALUES
(gen_random_uuid(),'Parent Teacher Meeting','Review student progress','2026-08-18 10:00:00+05:30','Gandhi Nagar Hall','22222222-2222-2222-2222-222222222222'),
(gen_random_uuid(),'Health Camp',          'Free medical check-up',  '2026-08-25 09:00:00+05:30','PHC Gandhi Nagar', '22222222-2222-2222-2222-222222222222')
ON CONFLICT DO NOTHING;

-- Stories seeding removed


-- ── Nehru Colony Center  (Staff / Radha Kumari) ────────────────────
-- Children
INSERT INTO children (id, child_name, age, gender, parent_name, parent_mobile, center_id) VALUES
(gen_random_uuid(),'Aditya Singh',   5,'Male',  'Rajesh Singh',   '9333111001','33333333-3333-3333-3333-333333333333'),
(gen_random_uuid(),'Ananya Joshi',   4,'Female','Pradeep Joshi',  '9333111002','33333333-3333-3333-3333-333333333333'),
(gen_random_uuid(),'Bhavesh Patel',  6,'Male',  'Amit Patel',     '9333111003','33333333-3333-3333-3333-333333333333'),
(gen_random_uuid(),'Deepika Rao',    3,'Female','Venkat Rao',     '9333111004','33333333-3333-3333-3333-333333333333'),
(gen_random_uuid(),'Ganesh Babu',    5,'Male',  'Ravi Babu',      '9333111005','33333333-3333-3333-3333-333333333333')
ON CONFLICT DO NOTHING;

-- Beneficiaries
INSERT INTO beneficiaries (id, name, category, mobile, address, center_id) VALUES
(gen_random_uuid(),'Saradha Bai',    'Pregnant Woman',  '9333222001','Lane 2, Nehru Colony',   '33333333-3333-3333-3333-333333333333'),
(gen_random_uuid(),'Tulasi Devi',    'Lactating Mother','9333222002','Ward 7, Nehru Colony',   '33333333-3333-3333-3333-333333333333'),
(gen_random_uuid(),'Usha Rani',      'Pregnant Woman',  '9333222003','Sector 4, Nehru Colony', '33333333-3333-3333-3333-333333333333')
ON CONFLICT DO NOTHING;

-- Stock
INSERT INTO stock_entries (id, item_name, quantity_received, quantity_distributed, remaining_quantity, min_quantity, unit, received_date, supplier, center_id) VALUES
(gen_random_uuid(),'Rice (kg)',     70, 10, 60, 25, 'kg',     '2024-07-01','Government Ration',  '33333333-3333-3333-3333-333333333333'),
(gen_random_uuid(),'Eggs',         150, 30,120, 30, 'units',  '2024-07-01','Government Supply',  '33333333-3333-3333-3333-333333333333'),
(gen_random_uuid(),'Dal (kg)',      25,  5, 20, 10, 'kg',     '2024-07-02','Government Supply',  '33333333-3333-3333-3333-333333333333'),
(gen_random_uuid(),'Dates',         20,  8, 12,  8, 'kg',     '2024-07-02','Government Supply',  '33333333-3333-3333-3333-333333333333')
ON CONFLICT (center_id, item_name) DO NOTHING;

-- Meetings
INSERT INTO meetings (id, title, description, meeting_date, location, center_id) VALUES
(gen_random_uuid(),'Nutrition Awareness Drive','Session on nutritious food for mothers and kids','2026-08-22 10:00:00+05:30','Nehru Colony Hall','33333333-3333-3333-3333-333333333333')
ON CONFLICT DO NOTHING;

-- Stories seeding removed

-- ── Verify ────────────────────────────────────────────────────────
SELECT center_id, COUNT(*) AS child_count  FROM children     GROUP BY center_id ORDER BY center_id;
SELECT center_id, COUNT(*) AS benef_count  FROM beneficiaries GROUP BY center_id ORDER BY center_id;
SELECT center_id, COUNT(*) AS stock_count  FROM stock_entries GROUP BY center_id ORDER BY center_id;
