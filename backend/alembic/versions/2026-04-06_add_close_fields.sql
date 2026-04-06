-- Add close_reason and satisfaction columns to tickets table
-- Created: 2026-04-06
-- Description: Add fields for ticket closure confirmation by creator

-- Add close_reason column (TEXT)
ALTER TABLE tickets 
ADD COLUMN IF NOT EXISTS close_reason TEXT;

-- Add satisfaction column (VARCHAR)
ALTER TABLE tickets 
ADD COLUMN IF NOT EXISTS satisfaction VARCHAR(50);

-- Migration complete
SELECT 'Added close_reason and satisfaction columns to tickets table' AS migration_status;
