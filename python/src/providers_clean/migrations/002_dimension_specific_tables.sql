-- =====================================================
-- Multi-Dimensional Embedding Support
-- Creates separate tables for different embedding dimensions
-- =====================================================

-- Clean up incorrectly named tables from previous migration attempts
DROP TABLE IF EXISTS archon_documents_768 CASCADE;
DROP TABLE IF EXISTS archon_documents_1536 CASCADE;
DROP TABLE IF EXISTS archon_documents_3072 CASCADE;
DROP VIEW IF EXISTS archon_documents CASCADE;

-- Create tables for common embedding dimensions (matching archon_crawled_pages structure)
-- 768 dimensions (Google text-embedding-004)
CREATE TABLE IF NOT EXISTS archon_crawled_pages_768 (
    id BIGSERIAL PRIMARY KEY,
    url VARCHAR NOT NULL,
    chunk_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_id TEXT NOT NULL,
    embedding VECTOR(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(url, chunk_number),
    FOREIGN KEY (source_id) REFERENCES archon_sources(source_id)
);

-- 1536 dimensions (OpenAI text-embedding-3-small, text-embedding-ada-002)  
CREATE TABLE IF NOT EXISTS archon_crawled_pages_1536 (
    id BIGSERIAL PRIMARY KEY,
    url VARCHAR NOT NULL,
    chunk_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_id TEXT NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(url, chunk_number),
    FOREIGN KEY (source_id) REFERENCES archon_sources(source_id)
);

-- 3072 dimensions (OpenAI text-embedding-3-large)
CREATE TABLE IF NOT EXISTS archon_crawled_pages_3072 (
    id BIGSERIAL PRIMARY KEY,
    url VARCHAR NOT NULL,
    chunk_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_id TEXT NOT NULL,
    embedding VECTOR(3072),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(url, chunk_number),
    FOREIGN KEY (source_id) REFERENCES archon_sources(source_id)
);

-- Create indexes for efficient similarity search  
-- Note: pgvector indexes have 2000 dimension limit, so 3072D table will use sequential scan
CREATE INDEX IF NOT EXISTS idx_archon_crawled_pages_768_embedding ON archon_crawled_pages_768 USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_archon_crawled_pages_1536_embedding ON archon_crawled_pages_1536 USING ivfflat (embedding vector_cosine_ops);
-- Skip vector index for 3072D table due to pgvector 2000 dimension limit - will use sequential scan

-- Create indexes for URL-based queries
CREATE INDEX IF NOT EXISTS idx_archon_crawled_pages_768_url ON archon_crawled_pages_768(url);
CREATE INDEX IF NOT EXISTS idx_archon_crawled_pages_1536_url ON archon_crawled_pages_1536(url);
CREATE INDEX IF NOT EXISTS idx_archon_crawled_pages_3072_url ON archon_crawled_pages_3072(url);

-- Create metadata indexes for filtering
CREATE INDEX IF NOT EXISTS idx_archon_crawled_pages_768_metadata ON archon_crawled_pages_768 USING gin(metadata);
CREATE INDEX IF NOT EXISTS idx_archon_crawled_pages_1536_metadata ON archon_crawled_pages_1536 USING gin(metadata);
CREATE INDEX IF NOT EXISTS idx_archon_crawled_pages_3072_metadata ON archon_crawled_pages_3072 USING gin(metadata);

-- Create source_id indexes
CREATE INDEX IF NOT EXISTS idx_archon_crawled_pages_768_source_id ON archon_crawled_pages_768(source_id);
CREATE INDEX IF NOT EXISTS idx_archon_crawled_pages_1536_source_id ON archon_crawled_pages_1536(source_id);
CREATE INDEX IF NOT EXISTS idx_archon_crawled_pages_3072_source_id ON archon_crawled_pages_3072(source_id);

-- Note: Existing data migration is skipped due to vector type casting limitations
-- If you need to migrate existing data, manually inspect the archon_documents table
-- and move data to the appropriate dimension-specific table based on your embedding model

-- Create a view that unions all dimension tables for backward compatibility
CREATE OR REPLACE VIEW archon_crawled_pages_all
WITH (security_invoker = true) AS
SELECT id, url, chunk_number, content, embedding, metadata, source_id, created_at, 768 as embedding_dimensions FROM archon_crawled_pages_768
UNION ALL
SELECT id, url, chunk_number, content, embedding, metadata, source_id, created_at, 1536 as embedding_dimensions FROM archon_crawled_pages_1536  
UNION ALL
SELECT id, url, chunk_number, content, embedding, metadata, source_id, created_at, 3072 as embedding_dimensions FROM archon_crawled_pages_3072;

-- Function to get the correct table name for a given dimension
CREATE OR REPLACE FUNCTION get_documents_table_for_dimensions(dims integer)
RETURNS text
LANGUAGE plpgsql
AS $$
BEGIN
    CASE dims
        WHEN 768 THEN RETURN 'archon_crawled_pages_768';
        WHEN 1536 THEN RETURN 'archon_crawled_pages_1536';
        WHEN 3072 THEN RETURN 'archon_crawled_pages_3072';
        ELSE RAISE EXCEPTION 'Unsupported embedding dimension: %. Supported: 768, 1536, 3072', dims;
    END CASE;
END;
$$;

-- Add RLS policies for the new tables (drop existing first to avoid conflicts)
ALTER TABLE archon_crawled_pages_768 ENABLE ROW LEVEL SECURITY;
ALTER TABLE archon_crawled_pages_1536 ENABLE ROW LEVEL SECURITY; 
ALTER TABLE archon_crawled_pages_3072 ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read access to archon_crawled_pages_768" ON archon_crawled_pages_768;
DROP POLICY IF EXISTS "Allow public read access to archon_crawled_pages_1536" ON archon_crawled_pages_1536;
DROP POLICY IF EXISTS "Allow public read access to archon_crawled_pages_3072" ON archon_crawled_pages_3072;

CREATE POLICY "Allow public read access to archon_crawled_pages_768"
  ON archon_crawled_pages_768 FOR SELECT
  USING (true);

CREATE POLICY "Allow public read access to archon_crawled_pages_1536"
  ON archon_crawled_pages_1536 FOR SELECT
  USING (true);

CREATE POLICY "Allow public read access to archon_crawled_pages_3072"
  ON archon_crawled_pages_3072 FOR SELECT
  USING (true);