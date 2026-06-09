-- ================================================================
--  STORIES TABLE UPGRADE
--  Adds: content_type, is_global, url_link columns
--  Makes stories visible to all users (not just same-center)
-- ================================================================

-- 1. Add new columns
ALTER TABLE stories
  ADD COLUMN IF NOT EXISTS content_type  VARCHAR(20) DEFAULT 'text'
                                         CHECK (content_type IN ('url','video','pdf','text')),
  ADD COLUMN IF NOT EXISTS is_global     BOOLEAN     DEFAULT TRUE,
  ADD COLUMN IF NOT EXISTS url_link      TEXT;        -- for content_type = 'url'

-- 2. Back-fill existing rows
UPDATE stories SET
  content_type = CASE
    WHEN youtube_url IS NOT NULL AND youtube_url <> '' THEN 'url'
    WHEN video_url   IS NOT NULL AND video_url   <> '' THEN 'video'
    WHEN pdf_url     IS NOT NULL AND pdf_url     <> '' THEN 'pdf'
    ELSE 'text'
  END,
  is_global = TRUE
WHERE content_type IS NULL OR content_type = 'text';

-- 3. Index for type filtering
CREATE INDEX IF NOT EXISTS idx_stories_content_type ON stories(content_type);
CREATE INDEX IF NOT EXISTS idx_stories_is_global    ON stories(is_global);

-- Verify
SELECT content_type, count(*) FROM stories GROUP BY content_type;
