-- Create ticket_comments table
CREATE TABLE IF NOT EXISTS ticket_comments (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER REFERENCES tickets(id),
    content TEXT NOT NULL,
    author VARCHAR(100),
    author_role VARCHAR(50),
    is_internal BOOLEAN DEFAULT true,
    attachments JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Create index on ticket_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_comments_ticket_id ON ticket_comments(ticket_id);
