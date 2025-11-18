-- ============================================================================
-- Schéma PostgreSQL pour aikoGPT
-- Base de données pour stocker projets, documents, transcriptions, 
-- états de workflows et résultats d'agents
-- ============================================================================

-- Extension pour la recherche full-text
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================================
-- TABLE: users
-- Table pour les utilisateurs (préparée pour migration future)
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE,
    email VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Index sur username pour recherche rapide
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- ============================================================================
-- TABLE: projects
-- 1 projet = 1 entreprise (company_name)
-- ============================================================================
CREATE TABLE IF NOT EXISTS projects (
    id BIGSERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL UNIQUE,
    company_info JSONB,
    created_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Index sur company_name pour recherche rapide
CREATE INDEX IF NOT EXISTS idx_projects_company_name ON projects(company_name);
-- Index GIN sur company_info pour recherche dans JSONB
CREATE INDEX IF NOT EXISTS idx_projects_company_info ON projects USING GIN(company_info);
-- Index sur created_at pour requêtes temporelles
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at);

-- ============================================================================
-- TABLE: documents
-- Métadonnées des documents (pas de données extraites)
-- ============================================================================
CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL, -- workshop, transcript, word_report
    file_metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Index FK sur project_id
CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id);
-- Index sur file_type pour filtrage
CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);
-- Index GIN sur file_metadata pour recherche dans JSONB
CREATE INDEX IF NOT EXISTS idx_documents_file_metadata ON documents USING GIN(file_metadata);
-- Index sur created_at
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);

-- ============================================================================
-- TABLE: workshops
-- Données extraites des fichiers Excel d'ateliers
-- ============================================================================
CREATE TABLE IF NOT EXISTS workshops (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    atelier_name VARCHAR(255) NOT NULL,
    raw_extract JSONB NOT NULL,  -- {use_case1: {text: "...", objective: "..."}, ...}
    aggregate JSONB,  -- Résultat WorkshopData après LLM (peut être NULL si pas encore traité)
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Index FK sur document_id
CREATE INDEX IF NOT EXISTS idx_workshops_document_id ON workshops(document_id);
-- Index sur atelier_name pour recherche rapide
CREATE INDEX IF NOT EXISTS idx_workshops_atelier_name ON workshops(atelier_name);
-- Index GIN sur raw_extract pour recherche dans JSONB
CREATE INDEX IF NOT EXISTS idx_workshops_raw_extract ON workshops USING GIN(raw_extract);
-- Index GIN sur aggregate pour recherche dans JSONB
CREATE INDEX IF NOT EXISTS idx_workshops_aggregate ON workshops USING GIN(aggregate);

-- ============================================================================
-- TABLE: word_extractions
-- Données extraites des rapports Word (besoins et use cases)
-- ============================================================================
CREATE TABLE IF NOT EXISTS word_extractions (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    extraction_type VARCHAR(50) NOT NULL,  -- 'needs' ou 'use_cases'
    data JSONB NOT NULL,  -- Données structurées extraites
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Index FK sur document_id
CREATE INDEX IF NOT EXISTS idx_word_extractions_document_id ON word_extractions(document_id);
-- Index sur extraction_type pour filtrage
CREATE INDEX IF NOT EXISTS idx_word_extractions_extraction_type ON word_extractions(extraction_type);
-- Index GIN sur data pour recherche dans JSONB
CREATE INDEX IF NOT EXISTS idx_word_extractions_data ON word_extractions USING GIN(data);
-- Index composite pour requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_word_extractions_document_type ON word_extractions(document_id, extraction_type);

-- ============================================================================
-- TABLE: transcripts
-- Interventions extraites des documents avec recherche full-text
-- ============================================================================
CREATE TABLE IF NOT EXISTS transcripts (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    speaker VARCHAR(255),
    timestamp VARCHAR(50),
    text TEXT NOT NULL,
    speaker_type VARCHAR(50), -- interviewer, interviewé, etc.
    search_vector TSVECTOR,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Index FK sur document_id
CREATE INDEX IF NOT EXISTS idx_transcripts_document_id ON transcripts(document_id);
-- Index sur speaker pour filtrage
CREATE INDEX IF NOT EXISTS idx_transcripts_speaker ON transcripts(speaker);
-- Index sur speaker_type
CREATE INDEX IF NOT EXISTS idx_transcripts_speaker_type ON transcripts(speaker_type);
-- Index GIN sur search_vector pour recherche full-text (CRITIQUE)
CREATE INDEX IF NOT EXISTS idx_transcripts_search_vector ON transcripts USING GIN(search_vector);

-- ============================================================================
-- TABLE: workflow_states
-- Checkpoints LangGraph pour partage entre workflows
-- ============================================================================
CREATE TABLE IF NOT EXISTS workflow_states (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    workflow_type VARCHAR(50) NOT NULL, -- need_analysis, atouts, executive_summary, rappel_mission
    thread_id VARCHAR(255) NOT NULL,
    state_data JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'running', -- running, paused, completed, failed
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE(project_id, workflow_type, thread_id)
);

-- Index FK sur project_id
CREATE INDEX IF NOT EXISTS idx_workflow_states_project_id ON workflow_states(project_id);
-- Index sur workflow_type pour filtrage
CREATE INDEX IF NOT EXISTS idx_workflow_states_workflow_type ON workflow_states(workflow_type);
-- Index sur thread_id pour recherche rapide
CREATE INDEX IF NOT EXISTS idx_workflow_states_thread_id ON workflow_states(thread_id);
-- Index sur status
CREATE INDEX IF NOT EXISTS idx_workflow_states_status ON workflow_states(status);
-- Index GIN sur state_data pour recherche dans JSONB
CREATE INDEX IF NOT EXISTS idx_workflow_states_state_data ON workflow_states USING GIN(state_data);
-- Index composite pour requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_workflow_states_project_workflow ON workflow_states(project_id, workflow_type);

-- ============================================================================
-- TABLE: agent_results
-- Résultats structurés des agents (needs, use_cases, atouts, etc.)
-- ============================================================================
CREATE TABLE IF NOT EXISTS agent_results (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    workflow_type VARCHAR(50) NOT NULL,
    result_type VARCHAR(50) NOT NULL, -- needs, use_cases, atouts, challenges, recommendations, maturity, etc.
    data JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'proposed', -- proposed, validated, rejected, final
    iteration_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Index FK sur project_id
CREATE INDEX IF NOT EXISTS idx_agent_results_project_id ON agent_results(project_id);
-- Index sur workflow_type
CREATE INDEX IF NOT EXISTS idx_agent_results_workflow_type ON agent_results(workflow_type);
-- Index sur result_type
CREATE INDEX IF NOT EXISTS idx_agent_results_result_type ON agent_results(result_type);
-- Index sur status
CREATE INDEX IF NOT EXISTS idx_agent_results_status ON agent_results(status);
-- Index GIN sur data pour recherche dans JSONB (CRITIQUE)
CREATE INDEX IF NOT EXISTS idx_agent_results_data ON agent_results USING GIN(data);
-- Index composite pour requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_agent_results_project_workflow_type ON agent_results(project_id, workflow_type, result_type);

-- ============================================================================
-- TRIGGERS: Mise à jour automatique de updated_at
-- ============================================================================

-- Fonction générique pour mettre à jour updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Appliquer le trigger sur les tables avec updated_at
CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_states_updated_at
    BEFORE UPDATE ON workflow_states
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_results_updated_at
    BEFORE UPDATE ON agent_results
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workshops_updated_at
    BEFORE UPDATE ON workshops
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- TRIGGERS: Recherche full-text sur transcripts
-- ============================================================================

-- Fonction pour mettre à jour le search_vector
CREATE OR REPLACE FUNCTION update_transcript_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    -- Construire le TSVECTOR à partir du texte et du speaker
    NEW.search_vector := 
        setweight(to_tsvector('french', COALESCE(NEW.text, '')), 'A') ||
        setweight(to_tsvector('french', COALESCE(NEW.speaker, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger pour mettre à jour search_vector à l'insertion et mise à jour
CREATE TRIGGER update_transcript_search_vector_trigger
    BEFORE INSERT OR UPDATE ON transcripts
    FOR EACH ROW
    EXECUTE FUNCTION update_transcript_search_vector();

-- ============================================================================
-- FONCTION: Recherche full-text dans transcripts
-- ============================================================================

CREATE OR REPLACE FUNCTION search_transcripts(
    search_query TEXT,
    project_id_filter BIGINT DEFAULT NULL,
    speaker_filter VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    id BIGINT,
    document_id BIGINT,
    speaker VARCHAR,
    "timestamp" VARCHAR,
    text TEXT,
    speaker_type VARCHAR,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id,
        t.document_id,
        t.speaker,
        t.timestamp,
        t.text,
        t.speaker_type,
        ts_rank(t.search_vector, plainto_tsquery('french', search_query)) AS rank
    FROM transcripts t
    WHERE 
        t.search_vector @@ plainto_tsquery('french', search_query)
        AND (project_id_filter IS NULL OR EXISTS (
            SELECT 1 FROM documents d 
            WHERE d.id = t.document_id 
            AND d.project_id = project_id_filter
        ))
        AND (speaker_filter IS NULL OR t.speaker = speaker_filter)
    ORDER BY rank DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTAIRES
-- ============================================================================

COMMENT ON TABLE users IS 'Table des utilisateurs (préparée pour migration future)';
COMMENT ON TABLE projects IS 'Projets (1 projet = 1 entreprise)';
COMMENT ON TABLE documents IS 'Métadonnées des documents (sans données extraites)';
COMMENT ON TABLE workshops IS 'Données extraites des fichiers Excel d''ateliers';
COMMENT ON TABLE word_extractions IS 'Données extraites des rapports Word (besoins et use cases)';
COMMENT ON TABLE transcripts IS 'Interventions extraites avec recherche full-text';
COMMENT ON TABLE workflow_states IS 'Checkpoints LangGraph pour partage entre workflows';
COMMENT ON TABLE agent_results IS 'Résultats structurés des agents IA';

COMMENT ON COLUMN projects.company_info IS 'Informations structurées de l''entreprise (secteur, CA, employés, description)';
COMMENT ON COLUMN workshops.raw_extract IS 'Données brutes extraites du fichier Excel (JSON avec use_case1, use_case2, etc.)';
COMMENT ON COLUMN workshops.aggregate IS 'Résultat WorkshopData après traitement LLM (peut être NULL si pas encore traité)';
COMMENT ON COLUMN word_extractions.extraction_type IS 'Type d''extraction: ''needs'' ou ''use_cases''';
COMMENT ON COLUMN word_extractions.data IS 'Données structurées extraites (JSONB)';
COMMENT ON COLUMN transcripts.search_vector IS 'Vecteur de recherche full-text (mis à jour automatiquement)';
COMMENT ON COLUMN workflow_states.state_data IS 'État complet du workflow LangGraph en JSONB';
COMMENT ON COLUMN agent_results.data IS 'Résultats structurés de l''agent en JSONB';

