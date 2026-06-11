"""entry.bar text -> non-nullable bar_id FK to bar

Existing entries are pointed at bar id 1. If no bar with id 1 exists (fresh DB,
or one where the OSM sync burned the first sequence ids), an "Unknown bar"
placeholder is inserted as id 1 (osm_type="manual", osm_id=0 to satisfy the
unique constraint). The next OSM sync closes it like any other non-OSM row,
removing it from the autocomplete while entries keep referencing it.

Revision ID: e7a91c2b4f3d
Revises: d5b01bf3e70d

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e7a91c2b4f3d"
down_revision: str | None = "d5b01bf3e70d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("entry", sa.Column("bar_id", sa.Integer(), nullable=True))
    # fallback venue for entries logged before the bar referential existed
    op.execute(
        """
        INSERT INTO bar (id, osm_id, osm_type, name, amenity, latitude, longitude, city, is_closed)
        SELECT 1, 0, 'manual', 'Unknown bar', 'bar', 48.8566, 2.3522, 'Paris', false
        WHERE NOT EXISTS (SELECT 1 FROM bar WHERE id = 1)
        """
    )
    # an explicit-id INSERT does not advance the serial sequence — realign it
    op.execute("SELECT setval('bar_id_seq', GREATEST((SELECT MAX(id) FROM bar), (SELECT last_value FROM bar_id_seq)))")
    op.execute("UPDATE entry SET bar_id = 1")
    op.alter_column("entry", "bar_id", nullable=False)
    op.create_index(op.f("ix_entry_bar_id"), "entry", ["bar_id"], unique=False)
    op.create_foreign_key("fk_entry_bar_id_bar", "entry", "bar", ["bar_id"], ["id"])
    op.drop_column("entry", "bar")


def downgrade() -> None:
    op.add_column("entry", sa.Column("bar", sa.TEXT(), nullable=True))
    # best effort: restore venue names from the referential
    op.execute("UPDATE entry SET bar = b.name FROM bar b WHERE entry.bar_id = b.id")
    op.drop_constraint("fk_entry_bar_id_bar", "entry", type_="foreignkey")
    op.drop_index(op.f("ix_entry_bar_id"), table_name="entry")
    op.drop_column("entry", "bar_id")
