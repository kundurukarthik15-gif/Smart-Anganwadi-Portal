-- ================================================================
-- SMART ANGANWADI PORTAL — DATABASE SCHEMA
-- Run this SQL in Supabase SQL Editor
-- ================================================================

-- 1. CENTERS TABLE
CREATE TABLE IF NOT EXISTS public.centers (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  center_name character varying NOT NULL,
  district character varying NOT NULL,
  mandal character varying NOT NULL,
  village character varying NOT NULL,
  address text,
  mobile character varying,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT centers_pkey PRIMARY KEY (id)
);

-- 2. USERS TABLE
CREATE TABLE IF NOT EXISTS public.users (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  full_name character varying NOT NULL,
  email character varying NOT NULL UNIQUE,
  password_hash text NOT NULL,
  mobile character varying,
  center_id uuid NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT users_pkey PRIMARY KEY (id),
  CONSTRAINT users_center_id_fkey FOREIGN KEY (center_id) REFERENCES public.centers(id)
);

-- 3. CHILDREN TABLE
CREATE TABLE IF NOT EXISTS public.children (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  child_name character varying NOT NULL,
  age integer NOT NULL CHECK (age >= 0 AND age <= 12),
  gender character varying NOT NULL CHECK (gender::text = ANY (ARRAY['Male'::character varying, 'Female'::character varying]::text[])),
  parent_name character varying,
  parent_mobile character varying,
  address text,
  center_id uuid NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  date_of_birth date,
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT children_pkey PRIMARY KEY (id),
  CONSTRAINT children_center_id_fkey FOREIGN KEY (center_id) REFERENCES public.centers(id)
);

-- 4. BENEFICIARIES TABLE
CREATE TABLE IF NOT EXISTS public.beneficiaries (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  name character varying NOT NULL,
  category character varying NOT NULL CHECK (category::text = ANY (ARRAY['Pregnant Woman'::character varying, 'Lactating Mother'::character varying]::text[])),
  mobile character varying,
  address text,
  center_id uuid NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT beneficiaries_pkey PRIMARY KEY (id),
  CONSTRAINT beneficiaries_center_id_fkey FOREIGN KEY (center_id) REFERENCES public.centers(id)
);

-- 5. STOCK ENTRIES TABLE
CREATE TABLE IF NOT EXISTS public.stock_entries (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  item_name character varying NOT NULL,
  quantity_received numeric DEFAULT 0,
  quantity_distributed numeric DEFAULT 0,
  remaining_quantity numeric DEFAULT 0 CHECK (remaining_quantity >= 0::numeric),
  min_quantity numeric DEFAULT 20,
  unit character varying DEFAULT 'units'::character varying,
  received_date date,
  supplier character varying,
  notes text,
  center_id uuid NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT stock_entries_pkey PRIMARY KEY (id),
  CONSTRAINT stock_entries_center_id_fkey FOREIGN KEY (center_id) REFERENCES public.centers(id)
);

-- 6. STOCK DISTRIBUTION TABLE
CREATE TABLE IF NOT EXISTS public.stock_distribution (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  stock_id uuid,
  item_name character varying NOT NULL,
  quantity numeric NOT NULL,
  distributed_to character varying NOT NULL,
  distribution_date date,
  distributed_by character varying,
  beneficiary_id uuid,
  center_id uuid NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT stock_distribution_pkey PRIMARY KEY (id),
  CONSTRAINT stock_distribution_stock_id_fkey FOREIGN KEY (stock_id) REFERENCES public.stock_entries(id),
  CONSTRAINT stock_distribution_beneficiary_id_fkey FOREIGN KEY (beneficiary_id) REFERENCES public.beneficiaries(id),
  CONSTRAINT stock_distribution_center_id_fkey FOREIGN KEY (center_id) REFERENCES public.centers(id)
);

-- 7. STOCK LOGS TABLE
CREATE TABLE IF NOT EXISTS public.stock_logs (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  stock_id uuid,
  action character varying NOT NULL,
  quantity numeric NOT NULL,
  detail text,
  center_id uuid,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT stock_logs_pkey PRIMARY KEY (id),
  CONSTRAINT stock_logs_stock_id_fkey FOREIGN KEY (stock_id) REFERENCES public.stock_entries(id),
  CONSTRAINT stock_logs_center_id_fkey FOREIGN KEY (center_id) REFERENCES public.centers(id)
);

-- 8. STORIES TABLE
CREATE TABLE IF NOT EXISTS public.stories (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  title character varying NOT NULL,
  language character varying NOT NULL CHECK (language::text = ANY (ARRAY['English'::character varying, 'Telugu'::character varying, 'Hindi'::character varying]::text[])),
  category character varying DEFAULT 'Moral Stories'::character varying,
  emoji character varying DEFAULT '📖'::character varying,
  preview text,
  has_audio boolean DEFAULT false,
  pdf_url text,
  audio_url text,
  video_url text,
  youtube_url text,
  center_id uuid NOT NULL,
  uploaded_by uuid,
  uploaded_at timestamp with time zone DEFAULT now(),
  CONSTRAINT stories_pkey PRIMARY KEY (id),
  CONSTRAINT stories_center_id_fkey FOREIGN KEY (center_id) REFERENCES public.centers(id),
  CONSTRAINT stories_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id)
);

-- 9. BMI RECORDS TABLE
CREATE TABLE IF NOT EXISTS public.bmi_records (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  child_id uuid,
  center_id uuid NOT NULL,
  recorded_by uuid,
  child_name character varying NOT NULL,
  age_at_measurement integer NOT NULL CHECK (age_at_measurement >= 0 AND age_at_measurement <= 12),
  gender character varying NOT NULL CHECK (gender::text = ANY (ARRAY['Male'::character varying, 'Female'::character varying]::text[])),
  height_cm numeric NOT NULL CHECK (height_cm >= 40::numeric AND height_cm <= 200::numeric),
  weight_kg numeric NOT NULL CHECK (weight_kg >= 2::numeric AND weight_kg <= 100::numeric),
  bmi_value numeric NOT NULL,
  bmi_category character varying NOT NULL CHECK (bmi_category::text = ANY (ARRAY['Severe Underweight'::character varying, 'Underweight'::character varying, 'Normal'::character varying, 'Overweight'::character varying, 'Obese'::character varying]::text[])),
  nutrition_status text,
  ai_recommendation jsonb,
  measurement_date date NOT NULL DEFAULT CURRENT_DATE,
  notes text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT bmi_records_pkey PRIMARY KEY (id),
  CONSTRAINT bmi_records_child_id_fkey FOREIGN KEY (child_id) REFERENCES public.children(id),
  CONSTRAINT bmi_records_center_id_fkey FOREIGN KEY (center_id) REFERENCES public.centers(id),
  CONSTRAINT bmi_records_recorded_by_fkey FOREIGN KEY (recorded_by) REFERENCES public.users(id)
);

-- 10. ATTENDANCE TABLE
CREATE TABLE IF NOT EXISTS public.attendance (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  child_id uuid NOT NULL,
  center_id uuid NOT NULL,
  attendance_date date NOT NULL DEFAULT CURRENT_DATE,
  status character varying NOT NULL CHECK (status::text = ANY (ARRAY['Present'::character varying::text, 'Absent'::character varying::text])),
  recorded_by uuid,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT attendance_pkey PRIMARY KEY (id),
  CONSTRAINT attendance_child_id_fkey FOREIGN KEY (child_id) REFERENCES public.children(id),
  CONSTRAINT attendance_center_id_fkey FOREIGN KEY (center_id) REFERENCES public.centers(id),
  CONSTRAINT attendance_recorded_by_fkey FOREIGN KEY (recorded_by) REFERENCES public.users(id)
);

-- 11. VACCINATIONS TABLE
CREATE TABLE IF NOT EXISTS public.vaccinations (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  child_id uuid NOT NULL,
  vaccine_name character varying NOT NULL,
  vaccine_purpose text NOT NULL,
  dose_number integer NOT NULL DEFAULT 1,
  due_date date NOT NULL,
  administered_date date,
  administered_by uuid,
  status character varying NOT NULL DEFAULT 'Upcoming' CHECK (status::text = ANY (ARRAY['Upcoming'::character varying, 'Completed'::character varying, 'Missed'::character varying]::text[])),
  notes text,
  batch_number character varying,
  remarks text,
  center_id uuid NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT vaccinations_pkey PRIMARY KEY (id),
  CONSTRAINT vaccinations_child_id_fkey FOREIGN KEY (child_id) REFERENCES public.children(id) ON DELETE CASCADE,
  CONSTRAINT vaccinations_center_id_fkey FOREIGN KEY (center_id) REFERENCES public.centers(id) ON DELETE CASCADE,
  CONSTRAINT vaccinations_administered_by_fkey FOREIGN KEY (administered_by) REFERENCES public.users(id) ON DELETE SET NULL
);

-- 11B. VACCINATION NOTIFICATIONS TABLE
CREATE TABLE IF NOT EXISTS public.vaccination_notifications (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  vaccination_id uuid,
  recipient_name character varying NOT NULL,
  recipient_mobile character varying NOT NULL,
  message_type character varying NOT NULL, -- 'WhatsApp', 'SMS', or 'WhatsApp & SMS'
  notification_type character varying NOT NULL, -- 'Manual', '3_days_before', '1_day_before', 'on_day', 'follow_up', 'emergency'
  status character varying NOT NULL DEFAULT 'Sent' CHECK (status::text = ANY (ARRAY['Sent'::character varying, 'Delivered'::character varying, 'Failed'::character varying]::text[])),
  error_message text,
  sent_at timestamp with time zone DEFAULT now(),
  center_id uuid NOT NULL,
  CONSTRAINT vaccination_notifications_pkey PRIMARY KEY (id),
  CONSTRAINT vaccination_notifications_vaccination_id_fkey FOREIGN KEY (vaccination_id) REFERENCES public.vaccinations(id) ON DELETE CASCADE,
  CONSTRAINT vaccination_notifications_center_id_fkey FOREIGN KEY (center_id) REFERENCES public.centers(id) ON DELETE CASCADE
);

-- 12. MATERNAL HEALTH RECORDS TABLE
CREATE TABLE IF NOT EXISTS public.maternal_health_records (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  beneficiary_id uuid NOT NULL,
  checkup_date date NOT NULL,
  weight_kg numeric,
  blood_pressure character varying,
  ifa_tablets_given integer DEFAULT 0,
  notes text,
  center_id uuid NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT maternal_health_records_pkey PRIMARY KEY (id),
  CONSTRAINT maternal_health_records_center_id_fkey FOREIGN KEY (center_id) REFERENCES public.centers(id),
  CONSTRAINT maternal_health_records_beneficiary_id_fkey FOREIGN KEY (beneficiary_id) REFERENCES public.beneficiaries(id)
);

-- 13. DAILY MEALS TABLE
CREATE TABLE IF NOT EXISTS public.daily_meals (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  center_id uuid NOT NULL,
  meal_date date NOT NULL DEFAULT CURRENT_DATE,
  children_served integer NOT NULL DEFAULT 0,
  beneficiaries_served integer NOT NULL DEFAULT 0,
  menu_served text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT daily_meals_pkey PRIMARY KEY (id),
  CONSTRAINT daily_meals_center_id_fkey FOREIGN KEY (center_id) REFERENCES public.centers(id)
);

-- ================================================================
-- CREATE INDEXES FOR BETTER PERFORMANCE
-- ================================================================

CREATE INDEX IF NOT EXISTS idx_users_center_id ON public.users(center_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_children_center_id ON public.children(center_id);
CREATE INDEX IF NOT EXISTS idx_beneficiaries_center_id ON public.beneficiaries(center_id);
CREATE INDEX IF NOT EXISTS idx_stock_entries_center_id ON public.stock_entries(center_id);
CREATE INDEX IF NOT EXISTS idx_stock_distribution_center_id ON public.stock_distribution(center_id);
CREATE INDEX IF NOT EXISTS idx_bmi_records_center_id ON public.bmi_records(center_id);
CREATE INDEX IF NOT EXISTS idx_bmi_records_child_id ON public.bmi_records(child_id);
CREATE INDEX IF NOT EXISTS idx_attendance_center_id ON public.attendance(center_id);
CREATE INDEX IF NOT EXISTS idx_attendance_child_id ON public.attendance(child_id);
CREATE INDEX IF NOT EXISTS idx_vaccinations_center_id ON public.vaccinations(center_id);
CREATE INDEX IF NOT EXISTS idx_vaccinations_child_id ON public.vaccinations(child_id);
CREATE INDEX IF NOT EXISTS idx_vaccinations_status ON public.vaccinations(status);
CREATE INDEX IF NOT EXISTS idx_vaccinations_due_date ON public.vaccinations(due_date);
CREATE INDEX IF NOT EXISTS idx_vaccination_notifications_vaccination_id ON public.vaccination_notifications(vaccination_id);
CREATE INDEX IF NOT EXISTS idx_vaccination_notifications_center_id ON public.vaccination_notifications(center_id);
CREATE INDEX IF NOT EXISTS idx_stories_center_id ON public.stories(center_id);
CREATE INDEX IF NOT EXISTS idx_daily_meals_center_id ON public.daily_meals(center_id);

-- ================================================================
-- INSTRUCTIONS
-- ================================================================
-- 1. Open Supabase Dashboard → Your Project → SQL Editor
-- 2. Copy all the SQL above (starting from CREATE TABLE)
-- 3. Paste into SQL Editor
-- 4. Click "Run" to execute
-- 5. All tables will be created automatically
-- 6. You can now use the registration page to create users and centers
