-- =====================================================
-- Available Models Table for Database-Driven Model Management
-- =====================================================
-- Store all available AI models in database instead of fetching from APIs
-- Enables better performance, reliability, and control
-- =====================================================

-- Create available_models table to store all model information
CREATE TABLE IF NOT EXISTS public.available_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Model identification
    provider TEXT NOT NULL, -- 'openai', 'google', 'anthropic', 'ollama', etc.
    model_id TEXT NOT NULL, -- 'gpt-4o', 'gemini-2.0-flash-exp', 'claude-3-5-sonnet'
    model_string TEXT NOT NULL, -- 'openai:gpt-4o' (provider:model_id)
    
    -- Display information
    display_name TEXT NOT NULL, -- 'OpenAI: GPT-4o'
    description TEXT, -- Model description
    
    -- Technical specifications
    context_length INTEGER, -- Maximum context window
    input_cost DECIMAL(12, 8), -- Cost per input token (per 1M tokens)
    output_cost DECIMAL(12, 8), -- Cost per output token (per 1M tokens)
    
    -- Capabilities
    supports_vision BOOLEAN DEFAULT false,
    supports_tools BOOLEAN DEFAULT false,
    supports_reasoning BOOLEAN DEFAULT false,
    is_embedding BOOLEAN DEFAULT false,
    
    -- Pricing classification
    is_free BOOLEAN DEFAULT false,
    cost_tier TEXT, -- 'free', 'low', 'medium', 'high'
    
    -- Management
    is_active BOOLEAN DEFAULT true, -- Can be manually disabled
    source TEXT DEFAULT 'openrouter', -- 'openrouter', 'manual', 'local'
    
    -- Tracking
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_model UNIQUE(provider, model_id),
    CONSTRAINT valid_model_string CHECK (model_string = provider || ':' || model_id),
    CONSTRAINT valid_cost_tier CHECK (cost_tier IN ('free', 'low', 'medium', 'high'))
);

-- Create indexes for efficient querying
CREATE INDEX idx_available_models_provider ON public.available_models(provider) WHERE is_active = true;
CREATE INDEX idx_available_models_type ON public.available_models(is_embedding, is_active);
CREATE INDEX idx_available_models_cost ON public.available_models(cost_tier) WHERE is_active = true;
CREATE INDEX idx_available_models_capabilities ON public.available_models(supports_vision, supports_tools) WHERE is_active = true;
CREATE INDEX idx_available_models_updated ON public.available_models(last_updated DESC);
CREATE INDEX idx_available_models_active ON public.available_models(is_active, provider);

-- =====================================================
-- ROW LEVEL SECURITY (RLS)
-- =====================================================

-- Enable RLS on available_models
ALTER TABLE public.available_models ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any
DROP POLICY IF EXISTS "Service role full access to available_models" ON public.available_models;

-- Service role full access policy
CREATE POLICY "Service role full access to available_models" 
    ON public.available_models
    FOR ALL 
    TO service_role
    USING (true)
    WITH CHECK (true);

-- =====================================================
-- VIEWS
-- =====================================================

-- View for active models only (inherits RLS)
CREATE OR REPLACE VIEW active_models AS
SELECT 
    id,
    provider,
    model_id,
    model_string,
    display_name,
    description,
    context_length,
    input_cost,
    output_cost,
    supports_vision,
    supports_tools,
    supports_reasoning,
    is_embedding,
    is_free,
    cost_tier,
    source,
    last_updated
FROM available_models
WHERE is_active = true
ORDER BY provider, 
         CASE cost_tier 
            WHEN 'free' THEN 1 
            WHEN 'low' THEN 2 
            WHEN 'medium' THEN 3 
            WHEN 'high' THEN 4 
            ELSE 5 
         END,
         display_name;

-- View for model statistics (inherits RLS)
CREATE OR REPLACE VIEW model_statistics AS
SELECT 
    provider,
    COUNT(*) as total_models,
    COUNT(*) FILTER (WHERE is_active = true) as active_models,
    COUNT(*) FILTER (WHERE is_embedding = true AND is_active = true) as embedding_models,
    COUNT(*) FILTER (WHERE is_embedding = false AND is_active = true) as llm_models,
    COUNT(*) FILTER (WHERE is_free = true AND is_active = true) as free_models,
    COUNT(*) FILTER (WHERE supports_vision = true AND is_active = true) as vision_models,
    COUNT(*) FILTER (WHERE supports_tools = true AND is_active = true) as tool_models,
    MAX(context_length) as max_context_length,
    MIN(input_cost) FILTER (WHERE input_cost > 0 AND is_active = true) as min_cost,
    MAX(input_cost) FILTER (WHERE is_active = true) as max_cost,
    MAX(last_updated) as last_sync
FROM available_models
GROUP BY provider
ORDER BY provider;

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to sync model data (upsert with conflict resolution)
CREATE OR REPLACE FUNCTION sync_model(
    p_provider TEXT,
    p_model_id TEXT,
    p_display_name TEXT,
    p_description TEXT DEFAULT NULL,
    p_context_length INTEGER DEFAULT NULL,
    p_input_cost DECIMAL(12, 8) DEFAULT NULL,
    p_output_cost DECIMAL(12, 8) DEFAULT NULL,
    p_supports_vision BOOLEAN DEFAULT false,
    p_supports_tools BOOLEAN DEFAULT false,
    p_supports_reasoning BOOLEAN DEFAULT false,
    p_is_embedding BOOLEAN DEFAULT false,
    p_is_free BOOLEAN DEFAULT false,
    p_cost_tier TEXT DEFAULT NULL,
    p_source TEXT DEFAULT 'openrouter'
) RETURNS UUID
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_model_string TEXT;
    v_id UUID;
BEGIN
    -- Generate model_string
    v_model_string := p_provider || ':' || p_model_id;
    
    -- Upsert model
    INSERT INTO available_models (
        provider, model_id, model_string, display_name, description,
        context_length, input_cost, output_cost,
        supports_vision, supports_tools, supports_reasoning, is_embedding,
        is_free, cost_tier, source, last_updated, is_active
    ) VALUES (
        p_provider, p_model_id, v_model_string, p_display_name, p_description,
        p_context_length, p_input_cost, p_output_cost,
        p_supports_vision, p_supports_tools, p_supports_reasoning, p_is_embedding,
        p_is_free, p_cost_tier, p_source, NOW(), true
    )
    ON CONFLICT (provider, model_id)
    DO UPDATE SET
        display_name = EXCLUDED.display_name,
        description = EXCLUDED.description,
        context_length = EXCLUDED.context_length,
        input_cost = EXCLUDED.input_cost,
        output_cost = EXCLUDED.output_cost,
        supports_vision = EXCLUDED.supports_vision,
        supports_tools = EXCLUDED.supports_tools,
        supports_reasoning = EXCLUDED.supports_reasoning,
        is_embedding = EXCLUDED.is_embedding,
        is_free = EXCLUDED.is_free,
        cost_tier = EXCLUDED.cost_tier,
        source = EXCLUDED.source,
        last_updated = NOW(),
        is_active = true -- Reactivate if it was disabled
    RETURNING id INTO v_id;
    
    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- Function to mark models as inactive (soft delete)
CREATE OR REPLACE FUNCTION deactivate_models_not_in_sync(
    p_source TEXT DEFAULT 'openrouter',
    p_sync_time TIMESTAMPTZ DEFAULT NOW()
) RETURNS INTEGER
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_count INTEGER;
BEGIN
    -- Mark models as inactive if they haven't been updated in this sync
    UPDATE available_models 
    SET is_active = false
    WHERE source = p_source 
      AND last_updated < p_sync_time
      AND is_active = true;
    
    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- GRANT PERMISSIONS
-- =====================================================

-- Grant usage on schema to service_role
GRANT USAGE ON SCHEMA public TO service_role;

-- Grant all privileges on the new table and functions
GRANT ALL PRIVILEGES ON TABLE public.available_models TO service_role;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- =====================================================
-- COMMENTS
-- =====================================================

COMMENT ON TABLE public.available_models IS 'Store all available AI models from various providers - Service key access only';
COMMENT ON FUNCTION sync_model IS 'Upsert model data during sync operations - SECURITY DEFINER function';
COMMENT ON FUNCTION deactivate_models_not_in_sync IS 'Mark stale models as inactive after sync - SECURITY DEFINER function';
COMMENT ON VIEW active_models IS 'Active models only with optimal ordering - inherits RLS from base table';
COMMENT ON VIEW model_statistics IS 'Aggregated statistics per provider - inherits RLS from base table';

-- =====================================================
-- INITIAL DATA POPULATION
-- =====================================================

-- Add some common local models (Ollama) that aren't in OpenRouter
INSERT INTO public.available_models (
    provider, model_id, model_string, display_name, description,
    context_length, input_cost, output_cost, is_embedding, is_free, cost_tier, source
) VALUES 
    ('ollama', 'llama3', 'ollama:llama3', 'Llama 3 (Local)', 'Local Llama 3 model', 8192, 0, 0, false, true, 'free', 'local'),
    ('ollama', 'mistral', 'ollama:mistral', 'Mistral (Local)', 'Local Mistral model', 8192, 0, 0, false, true, 'free', 'local'),
    ('ollama', 'codellama', 'ollama:codellama', 'Code Llama (Local)', 'Local Code Llama model', 8192, 0, 0, false, true, 'free', 'local'),
    ('ollama', 'phi3', 'ollama:phi3', 'Phi-3 (Local)', 'Local Microsoft Phi-3 model', 8192, 0, 0, false, true, 'free', 'local')
ON CONFLICT (provider, model_id) DO NOTHING;

-- =====================================================
-- NOTES
-- =====================================================
-- 1. This table stores all available models from all sources
-- 2. Models can be manually disabled via is_active flag
-- 3. Sync functions handle upserts and cleanup automatically
-- 4. Views provide convenient filtered access
-- 5. RLS ensures only service role can access the data
-- 6. Local models (Ollama) are managed separately from OpenRouter sync
-- =====================================================