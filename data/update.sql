-- Warning: No backup? No mercy. Data is priceless.
--
-- ================================================================================
-- 1.3.1 => 1.4.0(now)
-- ================================================================================
--
-- Update Plan:
--
-- 1. Table `state` add new column `stat_last_date` datetime not null, set value '2025-01-01 00:00:00'
--
--
BEGIN;

-- Create `state_tmp` table as a copy of `state` table
CREATE TABLE
  `state_tmp` AS
SELECT
  *
FROM
  `state`;

-- Delete `state` table data
DELETE FROM `state`;

-- Add new column to state table
ALTER TABLE `state`
ADD COLUMN `stat_last_date` DATETIME NOT NULL;

-- Copy data from `state_tmp` to `state` table
INSERT INTO
  `state`
SELECT
  `id`,
  `sync_follower_id`,
  `sync_follower_page`,
  `sync_following_id`,
  `sync_following_page`,
  `follow_user_since`,
  `unfollow_following_since`,
  '2025-01-01 00:00:00'
FROM
  `state_tmp`;

-- Drop `state_tmp` table
DROP TABLE `state_tmp`;

COMMIT;