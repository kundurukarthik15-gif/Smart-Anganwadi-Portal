-- ================================================================
-- SMART ANGANWADI PORTAL — migration_v6_auth.sql
-- Run this in your Supabase SQL Editor to apply database upgrades
-- ================================================================

-- Add profile_photo to users table if it doesn't exist
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS profile_photo VARCHAR(2048);
