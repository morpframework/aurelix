import databases
import sqlalchemy as sa
import fastapi
import pydantic
import datetime
import traceback
from ..utils import validate_types
import dectate
from transitions import Machine
import typing


from .base import Collection
from ..exc import SearchException

class SQLACollection(Collection):


    @validate_types
    def __init__(self, request: fastapi.Request, 
                 database: databases.Database, 
                 table: sa.Table):
        self.path = '/' + self.name
        self.request = request
        self.table = table
        self.db = database

    @validate_types
    def get_item_name(self, item: pydantic.BaseModel) -> str:
        if hasattr(self.table.c, 'name'):
            return item.name
        return str(item.id)

    @validate_types
    async def create(self, item: pydantic.BaseModel) -> pydantic.BaseModel:
        data = await self.transform_create_data(item)
        await self.before_create(data)
        query = self.table.insert().values(**data)
        new_id = await self.db.execute(query)
        item = await self.get_by_id(new_id)
        await self.after_create(item)
        return item

    async def _get_by_field(self, field, value):
        query = self.table.select().where(getattr(self.table.c, field)==value)
        item = await self.db.fetch_one(query)
        if item == None:
            return None
        item = self.Schema.model_validate(item._asdict())
        return item       
    
    @validate_types
    async def get_by_id(self, id: int):
        return await self._get_by_field('id', id)

    @validate_types
    async def get(self, identifier: str):
        if hasattr(self.table.c, 'name'):
            return await self._get_by_field('name', identifier)
        return await self.get_by_id(int(identifier))

    @validate_types
    async def search(self, query: str | None, offset: int = 0, limit: int | None = None, 
               order_by: list[tuple[str,str]] | None = None):
        
        db_query = self.table.select()
        if query: 
            filter = sa.text(query)
            db_query = db_query.where(filter)
        db_query = db_query.limit(limit).offset(offset)
        if order_by:
            orderby = []
            for c,d in order_by:
                column = c
                if d.lower() == 'desc':
                    column += ' desc'
                orderby.append(sa.text(column))
            db_query = db_query.order_by(*orderby)
        try:
            items = await self.db.fetch_all(db_query)
        except Exception as e:
            raise SearchException(str(e))
        
        items = [self.Schema.model_validate(i._asdict()) for i in items] 
        return items
    
    @validate_types
    async def count(self, query: str | None) -> int:
        db_query = sa.select([sa.func.count()]).select_from(self.table)
        if query: 
            filter = sa.text(query)
            db_query = db_query.where(filter)
        try:
            result = await self.db.fetch_one(db_query)
        except Exception as e:
            raise SearchException(str(e))
        return result[0]

    async def _update_by_field(self, field, value, item):
        data = await self.transform_update_data(item)
        await self.before_update(data)
        query = self.table.update().where(getattr(self.table.c, field)==value).values(**data)
        await self.db.execute(query)
        item = await self._get_by_field(field, value)
        await self.after_update(item)
        return item
    
    @validate_types
    async def update_by_id(self, id: int, item: pydantic.BaseModel):
        return await self._update_by_field('id', id, item)

    @validate_types
    async def update(self, name: str, item: pydantic.BaseModel):
        result = await self.update_by_id(int(name), item)
        return result

    async def _delete_by_field(self, field, value):
        item = await self._get_by_field(field, value)
        data = await self.transform_delete_data(item)
        await self.before_delete(item)
        query = self.table.delete().where(getattr(self.table.c, field)==value)
        await self.db.execute(query)
        await self.after_delete(data)
        return True       
    
    @validate_types
    async def delete_by_id(self, id: int):
        return await self._delete_by_field('id', id)

    @validate_types
    async def delete(self, name: str):
        return await self.delete_by_id(int(name))
