-- ================================================================
--  SMART ANGANWADI PORTAL — BMI Records Migration
--  Run this in your Supabase SQL Editor to add the bmi_records table
-- ================================================================

-- ── CREATE bmi_records TABLE ────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.bmi_records (
  id                  UUID         NOT NULL DEFAULT uuid_generate_v4(),
  child_id            UUID,
  center_id           UUID         NOT NULL,
  recorded_by         UUID,

  -- Child snapshot at time of measurement
  child_name          VARCHAR(255) NOT NULL,
  age_at_measurement  INTEGER      NOT NULL CHECK (age_at_measurement >= 0 AND age_at_measurement <= 12),
  gender              VARCHAR(10)  NOT NULL CHECK (gender IN ('Male', 'Female')),

  -- Measurements
  height_cm           NUMERIC(5,1) NOT NULL CHECK (height_cm >= 40 AND height_cm <= 200),
  weight_kg           NUMERIC(5,2) NOT NULL CHECK (weight_kg >= 2  AND weight_kg <= 100),

  -- Calculated (set by Flask backend)
  bmi_value           NUMERIC(5,2) NOT NULL,
  bmi_category        VARCHAR(30)  NOT NULL CHECK (
                        bmi_category IN (
                          'Severe Underweight',
                          'Underweight',
                          'Normal',
                          'Overweight',
                          'Obese'
                        )
                      ),
  nutrition_status    TEXT,

  -- AI Recommendation stored as JSON
  ai_recommendation   JSONB,

  -- Metadata
  measurement_date    DATE         NOT NULL DEFAULT CURRENT_DATE,
  notes               TEXT,
  created_at          TIMESTAMPTZ  DEFAULT NOW(),

  -- Primary key
  CONSTRAINT bmi_records_pkey PRIMARY KEY (id),

  -- Foreign keys
  CONSTRAINT bmi_records_child_id_fkey
    FOREIGN KEY (child_id)   REFERENCES public.children(id)  ON DELETE SET NULL,
  CONSTRAINT bmi_records_center_id_fkey
    FOREIGN KEY (center_id)  REFERENCES public.centers(id)   ON DELETE CASCADE,
  CONSTRAINT bmi_records_recorded_by_fkey
    FOREIGN KEY (recorded_by) REFERENCES public.users(id)    ON DELETE SET NULL
);

-- ── INDEXES ─────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_bmi_center_id      ON public.bmi_records (center_id);
CREATE INDEX IF NOT EXISTS idx_bmi_child_id       ON public.bmi_records (child_id);
CREATE INDEX IF NOT EXISTS idx_bmi_category       ON public.bmi_records (bmi_category);
CREATE INDEX IF NOT EXISTS idx_bmi_date           ON public.bmi_records (measurement_date);
CREATE INDEX IF NOT EXISTS idx_bmi_needs_attn     ON public.bmi_records (center_id, bmi_category)
  WHERE bmi_category IN ('Severe Underweight', 'Underweight');

-- ── ROW LEVEL SECURITY (RLS) ─────────────────────────────────────
ALTER TABLE public.bmi_records ENABLE ROW LEVEL SECURITY;

-- Allow all operations for authenticated users (service role bypasses RLS)
CREATE POLICY "bmi_records_all" ON public.bmi_records
  FOR ALL USING (true) WITH CHECK (true);

-- ── SEED DATA (8 sample BMI records matching the children table) ──
-- Replace center_id with your actual center UUID if needed.
-- These use the children inserted in schema.sql (adjust child_id UUIDs accordingly).

-- Example: Insert one record manually after you have real child UUIDs
-- INSERT INTO public.bmi_records
--   (child_id, center_id, child_name, age_at_measurement, gender,
--    height_cm, weight_kg, bmi_value, bmi_category, nutrition_status, measurement_date)
-- VALUES
--   ('your-child-uuid-here', 'your-center-uuid-here',
--    'Arjun Reddy', 5, 'Male', 105.0, 16.0, 14.5,
--    'Severe Underweight',
--    'Severely malnourished — immediate nutritional intervention required.',
--    '2024-07-01');

-- ── VERIFY ───────────────────────────────────────────────────────
-- Run this to confirm the table was created:
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'bmi_records'
-- ORDER BY ordinal_position;
