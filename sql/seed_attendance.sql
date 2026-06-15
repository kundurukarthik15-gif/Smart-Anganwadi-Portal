-- Run this query in your Supabase SQL Editor to seed dummy data into the attendance table.
-- It inserts attendance records for the last 5 days for all children in the database.

DO $$
DECLARE
  v_child_record RECORD;
  v_date DATE;
  v_status VARCHAR;
BEGIN
  -- Loop over the past 5 days, up to today
  FOR v_date IN 
    SELECT d::date FROM generate_series(CURRENT_DATE - INTERVAL '4 days', CURRENT_DATE, '1 day'::interval) d
  LOOP
    -- Loop over every child currently in the database
    FOR v_child_record IN SELECT id, center_id FROM children LOOP
      
      -- Randomly assign Present (80% chance) or Absent (20% chance)
      IF random() < 0.8 THEN
        v_status := 'Present';
      ELSE
        v_status := 'Absent';
      END IF;

      -- Insert the attendance record
      -- Using ON CONFLICT to avoid errors if the record already exists
      INSERT INTO public.attendance (child_id, center_id, attendance_date, status)
      VALUES (v_child_record.id, v_child_record.center_id, v_date, v_status)
      ON CONFLICT (child_id, attendance_date) 
      DO UPDATE SET status = EXCLUDED.status;

    END LOOP;
  END LOOP;
END $$;
