-- ================================================================
-- SMART ANGANWADI PORTAL — VACCINATION & ALERTS MIGRATION (v7)
-- Run this SQL in your Supabase Project SQL Editor
-- ================================================================

-- 1. DROP EXISTING VACCINATIONS IF IT EXISTS
-- (Re-creating it with additional required fields to support history, doses, batch numbers, and remarks)
DROP TABLE IF EXISTS public.vaccinations CASCADE;

-- 2. CREATE VACCINATIONS TABLE
CREATE TABLE public.vaccinations (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  child_id uuid NOT NULL,
  vaccine_name character varying NOT NULL,
  vaccine_purpose text NOT NULL,
  dose_number integer NOT NULL DEFAULT 1,
  due_date date NOT NULL,
  administered_date date,
  administered_by uuid, -- FK to users.id (Anganwadi worker)
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

-- 3. CREATE VACCINATION NOTIFICATIONS TABLE
-- (Used to log all parent alerts and prevent duplicate automated reminders)
CREATE TABLE public.vaccination_notifications (
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

-- 4. CREATE INDEXES FOR OPTIMAL QUERY PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_vaccinations_child_id ON public.vaccinations(child_id);
CREATE INDEX IF NOT EXISTS idx_vaccinations_center_id ON public.vaccinations(center_id);
CREATE INDEX IF NOT EXISTS idx_vaccinations_status ON public.vaccinations(status);
CREATE INDEX IF NOT EXISTS idx_vaccinations_due_date ON public.vaccinations(due_date);

CREATE INDEX IF NOT EXISTS idx_vaccination_notifications_vaccination_id ON public.vaccination_notifications(vaccination_id);
CREATE INDEX IF NOT EXISTS idx_vaccination_notifications_center_id ON public.vaccination_notifications(center_id);
CREATE INDEX IF NOT EXISTS idx_vaccination_notifications_sent_at ON public.vaccination_notifications(sent_at);
