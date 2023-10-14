import databases
import sqlalchemy as sa
import sqlalchemy_utils as sautils
import fastapi
import pydantic
import datetime
import traceback
from ..utils import validate_types
from ..dependencies import get_permission_identities
import dectate
from transitions import Machine
import typing
from .. import schema
from .. import exc
import os

from .base import BaseCollection
from ..exc import SearchException

class AsyncSQLACollection(BaseCollection):

    @validate_types
    def __init__(self, request: fastapi.Request, 
                 database: databases.Database, 
                 table: sa.Table):
        self.path = '/' + self.name
        self.request = request
        self.table = table
        self.db = database

    @validate_types
    async def create(self, item: pydantic.BaseModel, secure=True, modify_object_store_fields=False, modify_workflow_status=False) -> pydantic.BaseModel:
        data = await self.transform_create_data(item, secure=secure, modify_object_store_fields=modify_object_store_fields,
                                                modify_workflow_status=modify_workflow_status)
        await self.before_create(data)
        async with self.db.transaction() as txn:
            query = self.table.insert().values(**data)
            new_id = await self.db.execute(query)
            item = await self.get_by_id(new_id, secure=secure)
            if item is None:
                raise exc.Forbidden("You are not allowed to create this object")
        await self.after_create(item)
        return item

    async def _get_by_field(self, field, value, secure: bool = True):
        filters = []
        if secure:
            filters = await self.get_permission_filters()
            filters = [sa.text(f) for f in filters]

        filters.append(getattr(self.table.c, field)==value)
        query = self.table.select().where(sa.and_(*filters))
        item = await self.db.fetch_one(query)
        if item == None:
            if secure:
                insecure_item = await self._get_by_field(field, value, secure=False)
                if insecure_item:
                    raise exc.Forbidden("You are not allowed to access this object")
            return None
        item = self.Schema.model_validate(item._asdict())
        return item       
    
    @validate_types
    async def search(self, query: str | None, offset: int = 0, limit: int | None = None, 
               order_by: list[tuple[str,str]] | None = None, secure: bool =True):
        
        db_query = self.table.select()
        filters = []
        if secure:
            filters = await self.get_permission_filters()
            filters = [sa.text(f) for f in filters]
        if query: 
            filters.append(sa.text(query))
        if filters:
            db_query = db_query.where(sa.and_(*filters))
        db_query = db_query.limit(limit).offset(offset)
        if order_by:
            orderby = []
            for c,d in order_by:
                column = c
                if getattr(self.table.c, c, None) is None:
                    raise exc.ValidationError("Invalid sort field '%s'" % c)
                if d.lower() == 'desc':
                    column += ' desc'
                elif d.lower() == 'asc':
                    column += ' asc'
                else:
                    raise exc.ValidationError("Invalid sort direction '%s'" % d)
                orderby.append(sa.text(column))
            db_query = db_query.order_by(*orderby)
        try:
            items = await self.db.fetch_all(db_query)
        except Exception as e:
            raise SearchException(str(e))
        
        items = [self.Schema.model_validate(i._asdict()) for i in items] 
        return items
    
    @validate_types
    async def count(self, query: str | None, secure=True) -> int:
        db_query = sa.select([sa.func.count()]).select_from(self.table)
        filters  = []
        if secure:
            filters = await self.get_permission_filters()
            filters = [sa.text(f) for f in filters]

        if query: 
            filters.append(sa.text(query))
        if filters:
            db_query = db_query.where(sa.and_(*filters))
        try:
            result = await self.db.fetch_one(db_query)
        except Exception as e:
            raise SearchException(str(e))
        return result[0]

    async def _update_by_field(self, field, value, item: dict, secure: bool=True, modify_object_store_fields: bool = False, 
                               modify_workflow_status: bool = False):
        data = await self.transform_update_data(item, secure=secure,
                                                modify_object_store_fields=modify_object_store_fields,
                                                modify_workflow_status=modify_workflow_status)
        await self.before_update(data)
        filters = []
        if secure:
            filters = await self.get_permission_filters()
            filters = [sa.text(f) for f in filters]
        filters.append(getattr(self.table.c, field)==value)
        async with self.db.transaction() as txn:
            query = self.table.update().where(sa.and_(*filters)).values(**data)
            await self.db.execute(query)
            item = await self._get_by_field(field, value, secure)
            if item is None:
                raise exc.Forbidden("You are not allowed to update this object")
        await self.after_update(item)
        return item
    
    async def _delete_by_field(self, field, value, secure=True):
        item = await self._get_by_field(field, value, secure)
        if item is None:
            raise exc.Forbidden('You are not allowed to delete this object')
        data = await self.transform_delete_data(item, secure=secure)
        await self.before_delete(item)
        filters = []
        if secure:
            filters = await self.get_permission_filters()
            filters = [sa.text(f) for f in filters]
        filters.append(getattr(self.table.c, field)==value)
        query = self.table.delete().where(sa.and_(*filters))
        await self.db.execute(query)
        await self.after_delete(data)
        return True       
    
