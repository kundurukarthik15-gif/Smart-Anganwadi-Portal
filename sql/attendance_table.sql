-- SQL Query to create the Student Attendance table
-- This links to your existing `children`, `centers`, and `users` tables.

CREATE TABLE public.attendance (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  child_id uuid NOT NULL,
  center_id uuid NOT NULL,
  attendance_date date NOT NULL DEFAULT CURRENT_DATE,
  status character varying NOT NULL CHECK (status::text = ANY (ARRAY['Present'::character varying, 'Absent'::character varying]::text[])),
  recorded_by uuid,
  created_at timestamp with time zone DEFAULT now(),
  
  -- Primary Key
  CONSTRAINT attendance_pkey PRIMARY KEY (id),
  
  -- Foreign Keys
  CONSTRAINT attendance_child_id_fkey FOREIGN KEY (child_id) REFERENCES public.children(id) ON DELETE CASCADE,
  CONSTRAINT attendance_center_id_fkey FOREIGN KEY (center_id) REFERENCES public.centers(id) ON DELETE CASCADE,
  CONSTRAINT attendance_recorded_by_fkey FOREIGN KEY (recorded_by) REFERENCES public.users(id) ON DELETE SET NULL,
  
  -- Prevent duplicate attendance records for the same child on the same day
  CONSTRAINT attendance_unique_daily_record UNIQUE (child_id, attendance_date)
);

-- Optional: Create an index for faster querying by date and child
CREATE INDEX idx_attendance_date ON public.attendance (attendance_date);
CREATE INDEX idx_attendance_center_date ON public.attendance (center_id, attendance_date);
