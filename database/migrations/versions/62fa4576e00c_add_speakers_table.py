"""add_speakers_table

Revision ID: 62fa4576e00c
Revises: d2bfac0382f5
Create Date: 2025-11-18 10:01:29.529549

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '62fa4576e00c'
down_revision: Union[str, Sequence[str], None] = 'd2bfac0382f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Crée la table speakers et ajoute speaker_id à transcripts."""
    # Table: speakers
    op.create_table(
        'speakers',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=255), nullable=True),
        sa.Column('level', sa.String(length=50), nullable=True),  # 'direction', 'métier', 'inconnu'
        sa.Column('speaker_type', sa.String(length=50), nullable=False),  # 'interviewer' ou 'interviewé'
        sa.Column('project_id', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'name', name='uq_speakers_project_name')
    )
    
    # Index sur project_id pour recherche rapide
    op.create_index('idx_speakers_project_id', 'speakers', ['project_id'], unique=False)
    # Index sur speaker_type pour filtrage
    op.create_index('idx_speakers_speaker_type', 'speakers', ['speaker_type'], unique=False)
    # Index composite pour recherche par projet et type
    op.create_index('idx_speakers_project_type', 'speakers', ['project_id', 'speaker_type'], unique=False)
    
    # Ajouter colonne speaker_id à transcripts
    op.add_column('transcripts', sa.Column('speaker_id', sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        'fk_transcripts_speaker_id',
        'transcripts',
        'speakers',
        ['speaker_id'],
        ['id'],
        ondelete='SET NULL'
    )
    # Index sur speaker_id pour jointures rapides
    op.create_index('idx_transcripts_speaker_id', 'transcripts', ['speaker_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Supprime la colonne speaker_id et la table speakers."""
    # Supprimer l'index et la colonne speaker_id de transcripts
    op.drop_index('idx_transcripts_speaker_id', table_name='transcripts')
    op.drop_constraint('fk_transcripts_speaker_id', 'transcripts', type_='foreignkey')
    op.drop_column('transcripts', 'speaker_id')
    
    # Supprimer les index de speakers
    op.drop_index('idx_speakers_project_type', table_name='speakers')
    op.drop_index('idx_speakers_speaker_type', table_name='speakers')
    op.drop_index('idx_speakers_project_id', table_name='speakers')
    
    # Supprimer la table speakers
    op.drop_table('speakers')
