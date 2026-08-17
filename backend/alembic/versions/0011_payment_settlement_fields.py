"""Payment intent settlement fields.

Separates the on-chain settlement asset/amount from the listing's display
price/currency. No NGN->QUAI conversion is performed or assumed.
"""

from alembic import op
import sqlalchemy as sa

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("payment_intents") as batch:
        batch.add_column(
            sa.Column("display_price", sa.String(), nullable=True)
        )
        batch.add_column(
            sa.Column("display_currency", sa.String(), nullable=True)
        )
        batch.add_column(
            sa.Column("settlement_asset", sa.String(), nullable=True)
        )
        batch.add_column(
            sa.Column("settlement_amount_wei", sa.String(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("payment_intents") as batch:
        batch.drop_column("settlement_amount_wei")
        batch.drop_column("settlement_asset")
        batch.drop_column("display_currency")
        batch.drop_column("display_price")
