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

class SQLACollection(BaseCollection):

    name: str
    Schema: type[pydantic.BaseModel]
    permissionFilters: list[schema.PermissionFilterSpec]
    defaultFieldPermission: schema.FieldPermission

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
        async with self.db.transaction() as txn:
            query = self.table.insert().values(**data)
            new_id = await self.db.execute(query)
            item = await self.get_by_id(new_id)
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
    async def get_by_id(self, id: int, secure: bool = True):
        return await self._get_by_field('id', id, secure)

    @validate_types
    async def get(self, identifier: str, secure: bool=True):
        if hasattr(self.table.c, 'name'):
            return await self._get_by_field('name', identifier, secure)
        try:
            identifier = int(identifier)
        except ValueError:
            return None
        return await self.get_by_id(int(identifier), secure)

    
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

    async def _update_by_field(self, field, value, item, secure: bool=True):
        data = await self.transform_update_data(item)
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
    
    @validate_types
    async def update_by_id(self, id: int, item: pydantic.BaseModel, secure: bool = True):
        return await self._update_by_field('id', id, item, secure)

    @validate_types
    async def update(self, identifier: str, item: pydantic.BaseModel, secure: bool = True):
        if hasattr(self.table.c, 'name'):
            return await self._update_by_field('name', identifier, item, secure)
        try:
            identifier = int(identifier)
        except ValueError:
            return None
        return await self.update_by_id(int(identifier), item, secure)

    async def _delete_by_field(self, field, value, secure=True):
        item = await self._get_by_field(field, value, secure)
        if item is None:
            raise exc.Forbidden('You are not allowed to delete this object')
        data = await self.transform_delete_data(item)
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
    
    @validate_types
    async def delete_by_id(self, id: int, secure: bool = True):
        return await self._delete_by_field('id', id, secure)

    @validate_types
    async def delete(self, identifier: str, secure: bool = True):
        if hasattr(self.table.c, 'name'):
            return await self._delete_by_field('name', identifier, secure)
        try:
            identifier = int(identifier)
        except ValueError:
            return None
        return await self.delete_by_id(int(identifier), secure)

from sqlalchemy_utils.types.encrypted import encrypted_type

class EncryptedStringOptions(pydantic.BaseModel):
    engine: str
    key_env: str 

class EncryptedString(object):
    
    def __init__(self, field_name, app_spec: schema.AppSpec, field_spec: schema.FieldSpec):
        self.field_name = field_name
        self.app_spec = app_spec
        self.field_spec = field_spec
        
    def __call__(self, *args, **kwargs):
        if self.field_spec.dataType.options == None:
            raise exc.AurelixException("No options provided on 'encrypted-string' field '%s'" % self.field_name)
        options = EncryptedStringOptions.model_validate(self.field_spec.dataType.options) 
        engine_name = options.engine.lower()
        opts = {}
    
        if engine_name == 'fernet':
            opts['engine'] = encrypted_type.FernetEngine
        elif engine_name == 'aes':
            opts['engine'] = encrypted_type.AesEngine
        elif engine_name == 'aes-gcm':
            opts['engine'] = encrypted_type.AesGcmEngine
        else:
            raise exc.AurelixException("Unknown encryption engine %s" % engine_name)
        
        key = os.environ[options.key_env]
        opts['key'] = key
        
        return sautils.types.StringEncryptedType(sa.String(*args, **kwargs), **opts)