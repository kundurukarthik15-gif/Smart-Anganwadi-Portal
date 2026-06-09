-- ================================================================
-- SMART ANGANWADI PORTAL — Recommended Schema Upgrades
-- Run this script in your Supabase SQL Editor to apply improvements.
-- ================================================================

-- ── 1. STRUCTURAL IMPROVEMENTS ─────────────────────────────────

-- Replace 'age' with 'date_of_birth' in children table
-- We add the column, but don't drop 'age' immediately just in case your app still needs it.
-- You can eventually remove the 'age' column once your backend calculates it dynamically.
ALTER TABLE public.children ADD COLUMN IF NOT EXISTS date_of_birth DATE;

-- Add Unique Constraints to prevent duplicate data
ALTER TABLE public.attendance ADD CONSTRAINT unique_daily_attendance UNIQUE (child_id, attendance_date);
ALTER TABLE public.stock_entries ADD CONSTRAINT unique_center_item UNIQUE (center_id, item_name);
ALTER TABLE public.bmi_records ADD CONSTRAINT unique_daily_bmi UNIQUE (child_id, measurement_date);

-- Add updated_at columns
ALTER TABLE public.children ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE public.beneficiaries ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE public.stock_entries ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Create a generic function to automatically set updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Attach triggers to keep updated_at current automatically
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_children_updated_at') THEN
    CREATE TRIGGER set_children_updated_at
      BEFORE UPDATE ON public.children
      FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_beneficiaries_updated_at') THEN
    CREATE TRIGGER set_beneficiaries_updated_at
      BEFORE UPDATE ON public.beneficiaries
      FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_stock_entries_updated_at') THEN
    CREATE TRIGGER set_stock_entries_updated_at
      BEFORE UPDATE ON public.stock_entries
      FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
  END IF;
END
$$;


-- ── 2. NEW TABLES (ANGANWADI SPECIFIC FEATURES) ────────────────

-- A. Immunization / Vaccination Tracking
CREATE TABLE IF NOT EXISTS public.vaccinations (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  child_id uuid NOT NULL REFERENCES public.children(id) ON DELETE CASCADE,
  vaccine_name character varying NOT NULL,
  due_date date,
  administered_date date,
  status character varying DEFAULT 'Pending' CHECK (status IN ('Pending', 'Administered')),
  center_id uuid NOT NULL REFERENCES public.centers(id) ON DELETE CASCADE,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT unique_child_vaccine UNIQUE (child_id, vaccine_name)
);
CREATE INDEX IF NOT EXISTS idx_vaccinations_center_id ON public.vaccinations(center_id);

-- B. Maternal Health Tracking (Checkups & IFA tablets)
CREATE TABLE IF NOT EXISTS public.maternal_health_records (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  beneficiary_id uuid NOT NULL REFERENCES public.beneficiaries(id) ON DELETE CASCADE,
  checkup_date date NOT NULL,
  weight_kg numeric,
  blood_pressure character varying,
  ifa_tablets_given integer DEFAULT 0,
  notes text,
  center_id uuid NOT NULL REFERENCES public.centers(id) ON DELETE CASCADE,
  created_at timestamp with time zone DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_maternal_health_center_id ON public.maternal_health_records(center_id);

-- C. Daily Meals (Hot Cooked Meals) Tracker
CREATE TABLE IF NOT EXISTS public.daily_meals (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  center_id uuid NOT NULL REFERENCES public.centers(id) ON DELETE CASCADE,
  meal_date date NOT NULL DEFAULT CURRENT_DATE,
  children_served integer NOT NULL DEFAULT 0,
  beneficiaries_served integer NOT NULL DEFAULT 0,
  menu_served text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT unique_daily_meal UNIQUE (center_id, meal_date)
);
CREATE INDEX IF NOT EXISTS idx_daily_meals_center_id ON public.daily_meals(center_id);
