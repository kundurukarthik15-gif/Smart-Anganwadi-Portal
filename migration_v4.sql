-- ================================================================
--  SMART ANGANWADI PORTAL — migration_v4.sql
--  Run this in your Supabase SQL Editor to apply database upgrades
-- ================================================================

-- ── 1. UPDATE ATTENDANCE TABLE ──────────────────────────────────
-- Add photo_url to attendance table if it doesn't exist
ALTER TABLE public.attendance ADD COLUMN IF NOT EXISTS photo_url VARCHAR(2048);

-- ── 2. CREATE VILLAGE SURVEY TABLE ──────────────────────────────
CREATE TABLE IF NOT EXISTS public.village_survey (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    village_name      VARCHAR(255) NOT NULL,
    total_population  INTEGER NOT NULL CHECK (total_population >= 0),
    total_families    INTEGER NOT NULL CHECK (total_families >= 0),
    total_children    INTEGER NOT NULL CHECK (total_children >= 0),
    pregnant_women    INTEGER NOT NULL CHECK (pregnant_women >= 0),
    lactating_mothers INTEGER NOT NULL CHECK (lactating_mothers >= 0),
    survey_year       INTEGER NOT NULL,
    survey_month      INTEGER CHECK (survey_month >= 1 AND survey_month <= 12),
    center_id         UUID NOT NULL REFERENCES public.centers(id) ON DELETE CASCADE,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_monthly_survey UNIQUE (center_id, survey_year, survey_month)
);

CREATE INDEX IF NOT EXISTS idx_village_survey_center_id ON public.village_survey(center_id);

-- Enforce unique yearly surveys (where month is NULL) per center
CREATE UNIQUE INDEX IF NOT EXISTS unique_yearly_survey 
ON public.village_survey (center_id, survey_year) 
WHERE survey_month IS NULL;

-- ── 3. CREATE REPORTS TABLE ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.reports (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_type  VARCHAR(100) NOT NULL,
    pdf_url      TEXT NOT NULL,
    generated_by VARCHAR(255) NOT NULL,
    center_id    UUID NOT NULL REFERENCES public.centers(id) ON DELETE CASCADE,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reports_center_id ON public.reports(center_id);

-- ── 4. SEED SAMPLE SURVEYS ──────────────────────────────────────
INSERT INTO public.village_survey (id, village_name, total_population, total_families, total_children, pregnant_women, lactating_mothers, survey_year, survey_month, center_id) VALUES
    (
        uuid_generate_v4(), 
        'Rajiv Nagar', 
        1250, 
        310, 
        85, 
        12, 
        15, 
        2026, 
        4, 
        '11111111-1111-1111-1111-111111111111'
    ),
    (
        uuid_generate_v4(), 
        'Rajiv Nagar', 
        1265, 
        315, 
        90, 
        14, 
        12, 
        2026, 
        5, 
        '11111111-1111-1111-1111-111111111111'
    ),
    (
        uuid_generate_v4(), 
        'Rajiv Nagar', 
        1280, 
        320, 
        92, 
        15, 
        14, 
        2026, 
        6, 
        '11111111-1111-1111-1111-111111111111'
    )
ON CONFLICT DO NOTHING;
