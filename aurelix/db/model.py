import sqlalchemy as sa
import datetime
from . import metadata
import pydantic
from enum import Enum

def table(name, metadata, columns=None, indexes=None, constraints=None, *args):
    columns = columns or []
    indexes = indexes or []
    constraints = constraints or []

    columns = [
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('dateCreated', sa.DateTime, default=datetime.datetime.utcnow, index=True),
        sa.Column('dateModified', sa.DateTime, default=datetime.datetime.utcnow, index=True),
        sa.Column('creator', sa.String, nullable=True, index=True),
        sa.Column('editor', sa.String, nullable=True, index=True),
    ] + columns

    return sa.Table(
        name,
        metadata,
        *columns,
        *indexes,
        *args
    )


class CoreModel(pydantic.BaseModel):
    id: int | None = None
    dateCreated: datetime.datetime | None = None
    dateModified: datetime.datetime | None = None
    creator: str | None = None
    editor: str | None = None
