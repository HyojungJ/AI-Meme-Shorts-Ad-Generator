"""add generating_voice to workflow_execution status check

Revision ID: 20260207_0700
Revises: 20260205_0900
Create Date: 2026-02-07 07:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '20260207_0700'
down_revision = '20260205_0900'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE workflow_execution
        DROP CONSTRAINT IF EXISTS workflow_execution_status_check;
        """
    )
    op.execute(
        """
        ALTER TABLE workflow_execution
        ADD CONSTRAINT workflow_execution_status_check
        CHECK (
            (status)::text = ANY (
                (ARRAY[
                    'created'::character varying,
                    'generating_character'::character varying,
                    'generating_voice'::character varying,
                    'generating_scenario'::character varying,
                    'generating_video'::character varying,
                    'content_generating'::character varying,
                    'pending_approval'::character varying,
                    'approved'::character varying,
                    'rejected'::character varying,
                    'processing'::character varying,
                    'completed'::character varying,
                    'failed'::character varying,
                    'cancelled'::character varying
                ])::text[]
            )
        );
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE workflow_execution
        DROP CONSTRAINT IF EXISTS workflow_execution_status_check;
        """
    )
    op.execute(
        """
        ALTER TABLE workflow_execution
        ADD CONSTRAINT workflow_execution_status_check
        CHECK (
            (status)::text = ANY (
                (ARRAY[
                    'created'::character varying,
                    'generating_character'::character varying,
                    'generating_scenario'::character varying,
                    'generating_video'::character varying,
                    'content_generating'::character varying,
                    'pending_approval'::character varying,
                    'approved'::character varying,
                    'rejected'::character varying,
                    'processing'::character varying,
                    'completed'::character varying,
                    'failed'::character varying,
                    'cancelled'::character varying
                ])::text[]
            )
        );
        """
    )
