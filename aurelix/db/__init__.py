import databases
import sqlalchemy as sa
from ..settings import settings

database = databases.Database(settings.database_url)
metadata = sa.MetaData()
engine = sa.create_engine(
    settings.database_url, connect_args={"check_same_thread": False}
)
