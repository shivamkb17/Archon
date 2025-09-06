-- =====================================================
-- Add embedding_dimensions and batch_size columns to model_config
-- =====================================================

-- Add new columns to existing model_config table
ALTER TABLE public.model_config 
ADD COLUMN IF NOT EXISTS embedding_dimensions INTEGER,
ADD COLUMN IF NOT EXISTS batch_size INTEGER DEFAULT 100;

-- Update existing embedding services with correct dimensions
UPDATE public.model_config 
SET embedding_dimensions = 1536, batch_size = 100 
WHERE service_name IN ('embeddings', 'embedding') 
AND embedding_dimensions IS NULL;

-- Update embedding service to use Google text-embedding-004 with correct dimensions
UPDATE public.model_config 
SET model_string = 'google:text-embedding-004', embedding_dimensions = 768, batch_size = 100 
WHERE service_name = 'embedding';

-- Update embeddings service to use Google text-embedding-004 with correct dimensions  
UPDATE public.model_config 
SET model_string = 'google:text-embedding-004', embedding_dimensions = 768, batch_size = 100 
WHERE service_name = 'embeddings';