from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'update_schema_002'
down_revision: Union[str, None] = 'update_schema_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(),
                    nullable=False)
    
    op.alter_column('projects', 'user_id',
                    existing_type=sa.UUID(),
                    nullable=False)
    
    op.create_index('idx_user_email', 'users', ['email'], unique=True)
    op.create_index('idx_project_user', 'projects', ['user_id'])
    op.create_index('idx_project_domain', 'projects', ['domain'])

def downgrade() -> None:
    op.drop_index('idx_user_email')
    op.drop_index('idx_project_user')
    op.drop_index('idx_project_domain')
    
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(),
                    nullable=True)
    
    op.alter_column('projects', 'user_id',
                    existing_type=sa.UUID(),
                    nullable=True)