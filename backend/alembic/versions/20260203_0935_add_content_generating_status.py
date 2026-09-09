"""add_content_generating_status

Revision ID: 6e2f2b3d1c9a
Revises: f3a8b9c2d1e4
Create Date: 2026-02-03 09:35:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "6e2f2b3d1c9a"
down_revision = "f3a8b9c2d1e4"
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
