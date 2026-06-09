-- ================================================================
--  SMART ANGANWADI PORTAL — migration_v5.sql
--  Run this in your Supabase SQL Editor to apply database upgrades
-- ================================================================

CREATE TABLE IF NOT EXISTS public.villagers (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name           VARCHAR(255) NOT NULL,
    age            INTEGER NOT NULL CHECK (age >= 0),
    gender         VARCHAR(10) NOT NULL CHECK (gender IN ('Male', 'Female')),
    category       VARCHAR(50) NOT NULL CHECK (category IN ('Child', 'Pregnant Woman', 'Lactating Mother', 'General Resident')),
    contact_number VARCHAR(15),
    address        TEXT,
    center_id      UUID NOT NULL REFERENCES public.centers(id) ON DELETE CASCADE,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_villagers_center_id ON public.villagers(center_id);

ALTER TABLE public.villagers DISABLE ROW LEVEL SECURITY;

-- Seed some sample villagers for the default center
INSERT INTO public.villagers (id, name, age, gender, category, contact_number, address, center_id) VALUES
    (uuid_generate_v4(), 'Karthik Rao', 32, 'Male', 'General Resident', '9848022338', 'H.No 3-45, Rajiv Nagar', '11111111-1111-1111-1111-111111111111'),
    (uuid_generate_v4(), 'Sravani Goud', 26, 'Female', 'Pregnant Woman', '9848022339', 'H.No 5-12, Rajiv Nagar', '11111111-1111-1111-1111-111111111111'),
    (uuid_generate_v4(), 'Venkat Reddy', 45, 'Male', 'General Resident', '9848022340', 'H.No 12-8, Rajiv Nagar', '11111111-1111-1111-1111-111111111111'),
    (uuid_generate_v4(), 'Bhavana Kumari', 24, 'Female', 'Lactating Mother', '9848022341', 'H.No 1-72, Rajiv Nagar', '11111111-1111-1111-1111-111111111111'),
    (uuid_generate_v4(), 'Chinnu Reddy', 4, 'Male', 'Child', '9848022341', 'H.No 1-72, Rajiv Nagar', '11111111-1111-1111-1111-111111111111')
ON CONFLICT DO NOTHING;
