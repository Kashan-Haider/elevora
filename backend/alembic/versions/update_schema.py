"""update schema

Revision ID: update_schema_001
Revises: 12a542f6d4d6
Create Date: 2025-05-21 18:30:06.019751

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'update_schema_001'
down_revision: Union[str, None] = '12a542f6d4d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Update users table
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(),
                    nullable=False)
    
    # Update projects table
    op.alter_column('projects', 'user_id',
                    existing_type=sa.UUID(),
                    nullable=False)

def downgrade() -> None:
    # Revert users table changes
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(),
                    nullable=True)
    
    # Revert projects table changes
    op.alter_column('projects', 'user_id',
                    existing_type=sa.UUID(),
                    nullable=True)