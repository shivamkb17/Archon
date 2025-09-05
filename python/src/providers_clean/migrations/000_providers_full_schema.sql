-- =====================================================
-- Providers Feature: Consolidated Full Schema (DB-first)
-- Applies core tables, RLS, functions, views, and initial seeds
-- Access restricted to service_role (service key) only
-- Safe to run on a clean DB; uses IF EXISTS/IF NOT EXISTS and ON CONFLICT
-- =====================================================

-- ===============
-- Cleanup (idempotent)
-- ===============
DROP VIEW IF EXISTS public.active_backend_services CASCADE;
DROP VIEW IF EXISTS public.active_agents CASCADE;
DROP VIEW IF EXISTS public.active_services CASCADE;
DROP VIEW IF EXISTS public.deprecated_services CASCADE;
DROP VIEW IF EXISTS public.service_usage_summary CASCADE;
DROP VIEW IF EXISTS public.enhanced_model_usage CASCADE;
DROP VIEW IF EXISTS public.active_models CASCADE;
DROP VIEW IF EXISTS public.daily_usage_summary CASCADE;
DROP VIEW IF EXISTS public.active_model_config CASCADE;

DROP TABLE IF EXISTS public.available_models CASCADE;
DROP TABLE IF EXISTS public.service_registry CASCADE;
DROP TABLE IF EXISTS public.model_usage CASCADE;
DROP TABLE IF EXISTS public.api_keys CASCADE;
DROP TABLE IF EXISTS public.model_config CASCADE;

-- ===============
-- Core Tables
-- ===============

CREATE TABLE IF NOT EXISTS public.model_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name TEXT NOT NULL UNIQUE,
    model_string TEXT NOT NULL,
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by TEXT,
    CONSTRAINT valid_model_string CHECK (model_string LIKE '%:%')
);
CREATE INDEX IF NOT EXISTS idx_model_config_service ON public.model_config(service_name);

CREATE TABLE IF NOT EXISTS public.api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider TEXT NOT NULL UNIQUE,
    encrypted_key TEXT NOT NULL,
    base_url TEXT,
    headers JSONB,
    is_active BOOLEAN DEFAULT true,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON public.api_keys(provider) WHERE is_active = true;

CREATE TABLE IF NOT EXISTS public.model_usage (
    id UUID DEFAULT gen_random_uuid(),
    service_name TEXT NOT NULL,
    model_string TEXT NOT NULL,
    request_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    estimated_cost DECIMAL(10, 6) DEFAULT 0,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (service_name, model_string, period_start)
);
CREATE INDEX IF NOT EXISTS idx_model_usage_period ON public.model_usage(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_model_usage_service ON public.model_usage(service_name, period_start DESC);

-- ===============
-- Available Models
-- ===============
CREATE TABLE IF NOT EXISTS public.available_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider TEXT NOT NULL,
    model_id TEXT NOT NULL,
    model_string TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT,
    context_length INTEGER,
    input_cost DECIMAL(12, 8),
    output_cost DECIMAL(12, 8),
    supports_vision BOOLEAN DEFAULT false,
    supports_tools BOOLEAN DEFAULT false,
    supports_reasoning BOOLEAN DEFAULT false,
    is_embedding BOOLEAN DEFAULT false,
    is_free BOOLEAN DEFAULT false,
    cost_tier TEXT,
    is_active BOOLEAN DEFAULT true,
    source TEXT DEFAULT 'openrouter',
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_model UNIQUE(provider, model_id),
    CONSTRAINT valid_model_string_models CHECK (model_string = provider || ':' || model_id),
    CONSTRAINT valid_cost_tier CHECK (cost_tier IN ('free', 'low', 'medium', 'high'))
);
CREATE INDEX IF NOT EXISTS idx_available_models_provider ON public.available_models(provider) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_available_models_type ON public.available_models(is_embedding, is_active);
CREATE INDEX IF NOT EXISTS idx_available_models_cost ON public.available_models(cost_tier) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_available_models_capabilities ON public.available_models(supports_vision, supports_tools) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_available_models_updated ON public.available_models(last_updated DESC);
CREATE INDEX IF NOT EXISTS idx_available_models_active ON public.available_models(is_active, provider);

-- ===============
-- Service Registry
-- ===============
CREATE TABLE IF NOT EXISTS public.service_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    category TEXT NOT NULL CHECK (category IN ('agent', 'service')),
    service_type TEXT NOT NULL CHECK (service_type IN ('pydantic_ai', 'backend_service', 'embedding_service')),
    model_type TEXT NOT NULL CHECK (model_type IN ('llm', 'embedding')),
    location TEXT CHECK (location IN ('agents_server', 'main_server', 'external')),
    supports_temperature BOOLEAN DEFAULT true,
    supports_max_tokens BOOLEAN DEFAULT true,
    default_model TEXT,
    cost_profile TEXT CHECK (cost_profile IN ('low', 'medium', 'high')),
    expected_requests_per_day INTEGER DEFAULT 0,
    avg_tokens_per_request INTEGER DEFAULT 2000,
    is_active BOOLEAN DEFAULT true,
    is_deprecated BOOLEAN DEFAULT false,
    deprecation_reason TEXT,
    replacement_service TEXT,
    owner_team TEXT,
    contact_email TEXT,
    documentation_url TEXT,
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_used TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT valid_replacement CHECK ((is_deprecated = false) OR (is_deprecated = true AND replacement_service IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS idx_service_registry_active ON public.service_registry(is_active, service_type) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_service_registry_category ON public.service_registry(category, is_active);
CREATE INDEX IF NOT EXISTS idx_service_registry_model_type ON public.service_registry(model_type, is_active);
CREATE INDEX IF NOT EXISTS idx_service_registry_location ON public.service_registry(location) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_service_registry_cost ON public.service_registry(cost_profile) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_service_registry_deprecated ON public.service_registry(is_deprecated, updated_at);
CREATE INDEX IF NOT EXISTS idx_service_registry_team ON public.service_registry(owner_team) WHERE owner_team IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_service_registry_last_used ON public.service_registry(last_used DESC NULLS LAST);

-- ===============
-- RLS: Service key only
-- ===============
ALTER TABLE public.model_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.available_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.service_registry ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role full access to model_config" ON public.model_config;
DROP POLICY IF EXISTS "Service role full access to api_keys" ON public.api_keys;
DROP POLICY IF EXISTS "Service role full access to model_usage" ON public.model_usage;
DROP POLICY IF EXISTS "Service role full access to available_models" ON public.available_models;
DROP POLICY IF EXISTS "Service role full access to service_registry" ON public.service_registry;

CREATE POLICY "Service role full access to model_config" ON public.model_config FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access to api_keys" ON public.api_keys FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access to model_usage" ON public.model_usage FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access to available_models" ON public.available_models FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access to service_registry" ON public.service_registry FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Revoke all other access
GRANT USAGE ON SCHEMA public TO service_role;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO service_role;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM anon;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM authenticated;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM authenticated;

-- ===============
-- Functions (security definer)
-- ===============
CREATE OR REPLACE FUNCTION increment_usage(
    p_service TEXT,
    p_model TEXT,
    p_tokens INTEGER,
    p_cost NUMERIC,
    p_period_start TIMESTAMPTZ
) RETURNS void 
SECURITY INVOKER
SET search_path = public
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO model_usage (
        service_name, model_string, request_count, total_tokens, estimated_cost, period_start, period_end
    ) VALUES (
        p_service, p_model, 1, p_tokens, p_cost, p_period_start, p_period_start + INTERVAL '1 day'
    )
    ON CONFLICT (service_name, model_string, period_start)
    DO UPDATE SET
        request_count = model_usage.request_count + 1,
        total_tokens = model_usage.total_tokens + p_tokens,
        estimated_cost = model_usage.estimated_cost + p_cost;
END; $$;

CREATE OR REPLACE FUNCTION get_current_model(p_service TEXT)
RETURNS TEXT 
SECURITY INVOKER
SET search_path = public
LANGUAGE plpgsql AS $$
DECLARE v_model TEXT; BEGIN
    SELECT model_string INTO v_model FROM model_config WHERE service_name = p_service;
    RETURN v_model;
END; $$;

CREATE OR REPLACE FUNCTION public.get_daily_costs(start_date DATE)
RETURNS TABLE (
    date DATE,
    total_cost DECIMAL(10, 6),
    request_count BIGINT,
    total_tokens BIGINT
)
SECURITY INVOKER
SET search_path = public
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT DATE(mu.period_start) as date,
           SUM(mu.estimated_cost)::DECIMAL(10, 6) as total_cost,
           SUM(mu.request_count)::BIGINT as request_count,
           SUM(mu.total_tokens)::BIGINT as total_tokens
    FROM public.model_usage mu
    WHERE DATE(mu.period_start) >= start_date
    GROUP BY DATE(mu.period_start)
    ORDER BY date DESC;
END; $$;

-- Restrict function execution
REVOKE ALL ON FUNCTION public.get_daily_costs(DATE) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.get_daily_costs(DATE) TO service_role;
REVOKE ALL ON FUNCTION public.increment_usage(TEXT, TEXT, INTEGER, NUMERIC, TIMESTAMPTZ) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.increment_usage(TEXT, TEXT, INTEGER, NUMERIC, TIMESTAMPTZ) TO service_role;
REVOKE ALL ON FUNCTION public.get_current_model(TEXT) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.get_current_model(TEXT) TO service_role;

-- ===============
-- Views (inherit RLS)
-- ===============
CREATE OR REPLACE VIEW daily_usage_summary
WITH (security_invoker = on) AS
SELECT service_name, model_string, DATE(period_start) as date,
       SUM(request_count) as total_requests, SUM(total_tokens) as total_tokens, SUM(estimated_cost) as total_cost
FROM model_usage
GROUP BY service_name, model_string, DATE(period_start)
ORDER BY date DESC, service_name;

CREATE OR REPLACE VIEW active_model_config
WITH (security_invoker = on) AS
SELECT mc.service_name, mc.model_string, mc.temperature, mc.max_tokens,
       SPLIT_PART(mc.model_string, ':', 1) as provider,
       SPLIT_PART(mc.model_string, ':', 2) as model,
       ak.is_active as api_key_configured
FROM model_config mc
LEFT JOIN api_keys ak ON SPLIT_PART(mc.model_string, ':', 1) = ak.provider AND ak.is_active = true;

CREATE OR REPLACE VIEW active_models
WITH (security_invoker = on) AS
SELECT id, provider, model_id, model_string, display_name, description, context_length,
       input_cost, output_cost, supports_vision, supports_tools, supports_reasoning,
       is_embedding, is_free, cost_tier, source, last_updated
FROM available_models
WHERE is_active = true
ORDER BY provider, cost_tier, display_name;

CREATE OR REPLACE VIEW active_services
WITH (security_invoker = on) AS
SELECT id, service_name, display_name, description, icon, category, service_type, model_type,
       location, supports_temperature, supports_max_tokens, default_model, cost_profile,
       expected_requests_per_day, avg_tokens_per_request, owner_team, contact_email,
       documentation_url, first_seen, last_used, updated_at
FROM service_registry
WHERE is_active = true AND is_deprecated = false
ORDER BY category, service_type, display_name;

CREATE OR REPLACE VIEW active_agents
WITH (security_invoker = on) AS
SELECT * FROM service_registry
WHERE category = 'agent' AND is_active = true AND is_deprecated = false
ORDER BY service_type, display_name;

CREATE OR REPLACE VIEW active_backend_services
WITH (security_invoker = on) AS
SELECT * FROM service_registry
WHERE category = 'service' AND is_active = true AND is_deprecated = false
ORDER BY service_type, display_name;

CREATE OR REPLACE VIEW deprecated_services
WITH (security_invoker = on) AS
SELECT service_name, display_name, deprecation_reason, replacement_service, last_used, updated_at,
       EXTRACT(DAYS FROM (NOW() - updated_at)) as days_since_deprecation
FROM service_registry
WHERE is_deprecated = true
ORDER BY updated_at DESC;

-- Views used for registry discovery/validation
CREATE OR REPLACE VIEW unregistered_services
WITH (security_invoker = on) AS
SELECT mc.service_name,
       mc.model_string
FROM model_config mc
LEFT JOIN service_registry sr ON sr.service_name = mc.service_name
WHERE sr.service_name IS NULL
ORDER BY mc.service_name;

CREATE OR REPLACE VIEW unconfigured_services
WITH (security_invoker = on) AS
SELECT sr.service_name,
       sr.display_name,
       sr.category,
       sr.service_type,
       sr.model_type,
       sr.default_model,
       sr.updated_at
FROM service_registry sr
LEFT JOIN model_config mc ON mc.service_name = sr.service_name
WHERE mc.service_name IS NULL
ORDER BY sr.updated_at DESC;

-- ===============
-- Triggers: auto-register/update registry from model_config
-- ===============
CREATE OR REPLACE FUNCTION upsert_service_from_model_config()
RETURNS TRIGGER
SECURITY INVOKER
SET search_path = public
LANGUAGE plpgsql AS $$
DECLARE
    sname TEXT := NEW.service_name;
    mstr  TEXT := NEW.model_string;
    is_agent BOOLEAN := (sname LIKE '%_agent' OR sname LIKE 'agent_%');
    is_embedding BOOLEAN := (POSITION('embedding' IN sname) > 0 OR POSITION('embedding' IN mstr) > 0);
    v_category TEXT;
    v_service_type TEXT;
    v_model_type TEXT;
    v_location TEXT;
    v_supports_temperature BOOLEAN;
    v_supports_max_tokens BOOLEAN;
    v_icon TEXT;
BEGIN
    IF is_agent THEN
        v_category := 'agent';
        v_service_type := 'pydantic_ai';
        v_model_type := 'llm';
        v_location := 'agents_server';
        v_supports_temperature := TRUE;
        v_supports_max_tokens := TRUE;
        v_icon := '🤖';
    ELSIF is_embedding THEN
        v_category := 'service';
        v_service_type := 'embedding_service';
        v_model_type := 'embedding';
        v_location := 'main_server';
        v_supports_temperature := FALSE;
        v_supports_max_tokens := FALSE;
        v_icon := '🧩';
    ELSE
        v_category := 'service';
        v_service_type := 'backend_service';
        v_model_type := 'llm';
        v_location := 'main_server';
        v_supports_temperature := TRUE;
        v_supports_max_tokens := TRUE;
        v_icon := '🔧';
    END IF;

    INSERT INTO public.service_registry (
        service_name, display_name, description, icon, category, service_type, model_type,
        location, supports_temperature, supports_max_tokens, default_model, cost_profile, owner_team, updated_at
    ) VALUES (
        sname,
        INITCAP(REPLACE(sname, '_', ' ')),
        CONCAT('Auto-discovered using ', mstr),
        v_icon,
        v_category,
        v_service_type,
        v_model_type,
        v_location,
        v_supports_temperature,
        v_supports_max_tokens,
        mstr,
        'medium',
        'auto-discovered',
        NOW()
    )
    ON CONFLICT (service_name) DO UPDATE SET
        default_model = EXCLUDED.default_model,
        updated_at = NOW();

    RETURN NEW;
END; $$;

DROP TRIGGER IF EXISTS trg_upsert_registry_on_model_config_insert ON public.model_config;
CREATE TRIGGER trg_upsert_registry_on_model_config_insert
AFTER INSERT ON public.model_config
FOR EACH ROW
EXECUTE FUNCTION upsert_service_from_model_config();

DROP TRIGGER IF EXISTS trg_upsert_registry_on_model_config_update ON public.model_config;
CREATE TRIGGER trg_upsert_registry_on_model_config_update
AFTER UPDATE OF model_string ON public.model_config
FOR EACH ROW
EXECUTE FUNCTION upsert_service_from_model_config();

-- ===============
-- Seed initial model_config (no local defaults in code)
-- ===============
INSERT INTO public.model_config (service_name, model_string, temperature, max_tokens, updated_at, updated_by) VALUES
    ('document_agent',       'openai:gpt-4o',                             0.7, NULL, NOW(), 'seed'),
    ('rag_agent',            'openai:gpt-4o-mini',                        0.7, NULL, NOW(), 'seed'),
    ('task_agent',           'openai:gpt-4o',                             0.7, NULL, NOW(), 'seed'),
    ('chat_agent',           'openai:gpt-4o',                             0.7, NULL, NOW(), 'seed'),
    ('code_agent',           'anthropic:claude-3-5-sonnet-20241022',      0.7, NULL, NOW(), 'seed'),
    ('vision_agent',         'openai:gpt-4o',                             0.7, NULL, NOW(), 'seed'),
    ('embeddings',           'openai:text-embedding-3-small',             0.0, NULL, NOW(), 'seed'),
    ('embedding',            'openai:text-embedding-ada-002',             0.0, NULL, NOW(), 'seed'),
    ('contextual_embedding', 'openai:gpt-4o-mini',                         0.3, NULL, NOW(), 'seed'),
    ('source_summary',       'openai:gpt-4o-mini',                         0.5, NULL, NOW(), 'seed'),
    ('code_summary',         'anthropic:claude-3-haiku-20240307',         0.3, NULL, NOW(), 'seed'),
    ('code_analysis',        'anthropic:claude-3-haiku-20240307',         0.2, NULL, NOW(), 'seed'),
    ('validation',           'openai:gpt-3.5-turbo',                      0.0, NULL, NOW(), 'seed'),
    ('summary_generation',   'openai:gpt-4o-mini',                         0.5, NULL, NOW(), 'seed'),
    ('llm_primary',          'openai:gpt-4o',                             0.7, NULL, NOW(), 'seed'),
    ('llm_secondary',        'openai:gpt-4o-mini',                         0.7, NULL, NOW(), 'seed')
ON CONFLICT (service_name) DO NOTHING;

-- Notes:
-- 1) Registry seeding is not included; call the app endpoint to discover and register
--    from model_config: POST /api/providers/services/registry/initialize
-- 2) All access is restricted to service_role; anon/authenticated have no privileges
