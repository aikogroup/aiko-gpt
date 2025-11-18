"""initial_schema

Revision ID: d2bfac0382f5
Revises: 
Create Date: 2025-11-17 17:37:28.739179

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd2bfac0382f5'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Crée toutes les tables initiales."""
    # Extension pour la recherche full-text
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    
    # Table: users
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    op.create_index('idx_users_username', 'users', ['username'], unique=False)
    
    # Table: projects
    op.create_table(
        'projects',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('company_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_name')
    )
    op.create_index('idx_projects_company_name', 'projects', ['company_name'], unique=False)
    op.create_index('idx_projects_company_info', 'projects', ['company_info'], unique=False, postgresql_using='gin')
    op.create_index('idx_projects_created_at', 'projects', ['created_at'], unique=False)
    
    # Table: documents
    op.create_table(
        'documents',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.BigInteger(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_documents_project_id', 'documents', ['project_id'], unique=False)
    op.create_index('idx_documents_file_type', 'documents', ['file_type'], unique=False)
    op.create_index('idx_documents_file_metadata', 'documents', ['file_metadata'], unique=False, postgresql_using='gin')
    op.create_index('idx_documents_created_at', 'documents', ['created_at'], unique=False)
    
    # Table: workshops
    op.create_table(
        'workshops',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_id', sa.BigInteger(), nullable=False),
        sa.Column('atelier_name', sa.String(length=255), nullable=False),
        sa.Column('raw_extract', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('aggregate', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_workshops_document_id', 'workshops', ['document_id'], unique=False)
    op.create_index('idx_workshops_atelier_name', 'workshops', ['atelier_name'], unique=False)
    op.create_index('idx_workshops_raw_extract', 'workshops', ['raw_extract'], unique=False, postgresql_using='gin')
    op.create_index('idx_workshops_aggregate', 'workshops', ['aggregate'], unique=False, postgresql_using='gin')
    
    # Table: word_extractions
    op.create_table(
        'word_extractions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_id', sa.BigInteger(), nullable=False),
        sa.Column('extraction_type', sa.String(length=50), nullable=False),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_word_extractions_document_id', 'word_extractions', ['document_id'], unique=False)
    op.create_index('idx_word_extractions_extraction_type', 'word_extractions', ['extraction_type'], unique=False)
    op.create_index('idx_word_extractions_data', 'word_extractions', ['data'], unique=False, postgresql_using='gin')
    op.create_index('idx_word_extractions_document_type', 'word_extractions', ['document_id', 'extraction_type'], unique=False)
    
    # Table: transcripts
    op.create_table(
        'transcripts',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_id', sa.BigInteger(), nullable=False),
        sa.Column('speaker', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.String(length=50), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('speaker_type', sa.String(length=50), nullable=True),
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_transcripts_document_id', 'transcripts', ['document_id'], unique=False)
    op.create_index('idx_transcripts_speaker', 'transcripts', ['speaker'], unique=False)
    op.create_index('idx_transcripts_speaker_type', 'transcripts', ['speaker_type'], unique=False)
    op.create_index('idx_transcripts_search_vector', 'transcripts', ['search_vector'], unique=False, postgresql_using='gin')
    
    # Table: workflow_states
    op.create_table(
        'workflow_states',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.BigInteger(), nullable=False),
        sa.Column('workflow_type', sa.String(length=50), nullable=False),
        sa.Column('thread_id', sa.String(length=255), nullable=False),
        sa.Column('state_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='running', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'workflow_type', 'thread_id', name='uq_workflow_states_project_workflow_thread')
    )
    op.create_index('idx_workflow_states_project_id', 'workflow_states', ['project_id'], unique=False)
    op.create_index('idx_workflow_states_workflow_type', 'workflow_states', ['workflow_type'], unique=False)
    op.create_index('idx_workflow_states_thread_id', 'workflow_states', ['thread_id'], unique=False)
    op.create_index('idx_workflow_states_status', 'workflow_states', ['status'], unique=False)
    op.create_index('idx_workflow_states_state_data', 'workflow_states', ['state_data'], unique=False, postgresql_using='gin')
    op.create_index('idx_workflow_states_project_workflow', 'workflow_states', ['project_id', 'workflow_type'], unique=False)
    
    # Table: agent_results
    op.create_table(
        'agent_results',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.BigInteger(), nullable=False),
        sa.Column('workflow_type', sa.String(length=50), nullable=False),
        sa.Column('result_type', sa.String(length=50), nullable=False),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='proposed', nullable=False),
        sa.Column('iteration_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_agent_results_project_id', 'agent_results', ['project_id'], unique=False)
    op.create_index('idx_agent_results_workflow_type', 'agent_results', ['workflow_type'], unique=False)
    op.create_index('idx_agent_results_result_type', 'agent_results', ['result_type'], unique=False)
    op.create_index('idx_agent_results_status', 'agent_results', ['status'], unique=False)
    op.create_index('idx_agent_results_data', 'agent_results', ['data'], unique=False, postgresql_using='gin')
    op.create_index('idx_agent_results_project_workflow_type', 'agent_results', ['project_id', 'workflow_type', 'result_type'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Supprime toutes les tables."""
    op.drop_index('idx_agent_results_project_workflow_type', table_name='agent_results')
    op.drop_index('idx_agent_results_data', table_name='agent_results')
    op.drop_index('idx_agent_results_status', table_name='agent_results')
    op.drop_index('idx_agent_results_result_type', table_name='agent_results')
    op.drop_index('idx_agent_results_workflow_type', table_name='agent_results')
    op.drop_index('idx_agent_results_project_id', table_name='agent_results')
    op.drop_table('agent_results')
    
    op.drop_index('idx_workflow_states_project_workflow', table_name='workflow_states')
    op.drop_index('idx_workflow_states_state_data', table_name='workflow_states')
    op.drop_index('idx_workflow_states_status', table_name='workflow_states')
    op.drop_index('idx_workflow_states_thread_id', table_name='workflow_states')
    op.drop_index('idx_workflow_states_workflow_type', table_name='workflow_states')
    op.drop_index('idx_workflow_states_project_id', table_name='workflow_states')
    op.drop_table('workflow_states')
    
    op.drop_index('idx_transcripts_search_vector', table_name='transcripts')
    op.drop_index('idx_transcripts_speaker_type', table_name='transcripts')
    op.drop_index('idx_transcripts_speaker', table_name='transcripts')
    op.drop_index('idx_transcripts_document_id', table_name='transcripts')
    op.drop_table('transcripts')
    
    op.drop_index('idx_word_extractions_document_type', table_name='word_extractions')
    op.drop_index('idx_word_extractions_data', table_name='word_extractions')
    op.drop_index('idx_word_extractions_extraction_type', table_name='word_extractions')
    op.drop_index('idx_word_extractions_document_id', table_name='word_extractions')
    op.drop_table('word_extractions')
    
    op.drop_index('idx_workshops_aggregate', table_name='workshops')
    op.drop_index('idx_workshops_raw_extract', table_name='workshops')
    op.drop_index('idx_workshops_atelier_name', table_name='workshops')
    op.drop_index('idx_workshops_document_id', table_name='workshops')
    op.drop_table('workshops')
    
    op.drop_index('idx_documents_created_at', table_name='documents')
    op.drop_index('idx_documents_file_metadata', table_name='documents')
    op.drop_index('idx_documents_file_type', table_name='documents')
    op.drop_index('idx_documents_project_id', table_name='documents')
    op.drop_table('documents')
    
    op.drop_index('idx_projects_created_at', table_name='projects')
    op.drop_index('idx_projects_company_info', table_name='projects')
    op.drop_index('idx_projects_company_name', table_name='projects')
    op.drop_table('projects')
    
    op.drop_index('idx_users_username', table_name='users')
    op.drop_table('users')
    
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
