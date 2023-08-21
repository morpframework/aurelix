from transitions.extensions.asyncio import AsyncMachine
import dectate
from ..utils import validate_types
import pydantic
import fastapi
import datetime
from .. import exc
from .. import schema
from ..dependencies import get_userinfo, get_permission_identities
import typing

class StateMachine(object):

    field: str
    states: list[str]
    transitions: list[dict[str, str | list[str]]]

    def __init__(self, request: fastapi.Request, item):
        self.request = request
        self.item = item
        self.machine = AsyncMachine(self, 
                               states=self.states, 
                               transitions=self.transitions,
                               initial=self.state or self.states[0])

    def get_state(self):
        return getattr(self.item, self.field)
    
    def set_state(self, value):
        setattr(self.item, self.field, value)

    state = property(get_state, set_state)

class ViewAction(dectate.Action):
    config = {
        'views': dict
    }

    def __init__(self, path, method, **kwargs):
        self.path = path
        self.method = method.lower()
        self.kwargs = kwargs

    def identifier(self, views):
        return (self.path, self.method)
    
    def perform(self, obj, views):
        views[(self.path, self.method)] = {
                'method': self.method,
                'path': self.path,
                'options': self.kwargs,
                'function': obj
        }

class ExtensibleViewsApp(dectate.App):

    view = dectate.directive(ViewAction)

    @classmethod
    def routes(cls):
        dectate.commit(cls)
        views = cls.config.views
        return sorted(views.values(), key=lambda v: len(v['path']))
    
    @classmethod
    def get_directive_methods(cls):
        # workaround with manual specification because this conflicts with pydantic
        yield 'view', cls.view
 
class BaseCollection(ExtensibleViewsApp):
    name: str
    Schema: type[pydantic.BaseModel]
    StateMachine: type[StateMachine]
    permissionFilters: list[schema.PermissionFilterSpec]
    defaultFieldPermission: schema.FieldPermission

    @validate_types
    def __init__(self, request: fastapi.Request):
        self.request = request

    @validate_types
    def get_item_name(self, item: pydantic.BaseModel) -> str:
        raise NotImplementedError

    def url(self, item=None):
        comps = [str(self.request.base_url)[:-1]]
        if self.request.scope['root_path']:
            comps.append(self.request.scope['root_path'])
        comps.append(self.name)
        if item:
            comps.append(self.get_item_name(item))
        return '/'.join(comps)

    @validate_types
    async def create(self, item: pydantic.BaseModel) -> pydantic.BaseModel:
        raise NotImplementedError

    @validate_types
    async def get_by_id(self, id: int):
        raise NotImplementedError

    @validate_types
    async def get(self, name: str):
        raise NotImplementedError

    @validate_types
    async def search(self, query: str | None, offset: int = 0, limit: int | None = None, 
               order_by: list[tuple[str,str]] | None = None):
        raise NotImplementedError

    @validate_types
    async def update_by_id(self, id: int, item: pydantic.BaseModel):
        raise NotImplementedError

    @validate_types
    async def update(self, name: str, item: pydantic.BaseModel):
        raise NotImplementedError

    @validate_types
    async def delete_by_id(self, id: int):
        raise NotImplementedError

    @validate_types
    async def delete(self, name: str):
        raise NotImplementedError

    async def get_permission_filters(self) -> list[str]:
        if not self.permissionFilters:
            return []
        
        identities = await get_permission_identities(self.request)
        has_filter = False
        for f in self.permissionFilters:
            if not f.whereFilter:
                continue
            has_filter = True
            if '*' in f.identities:
                return [f.whereFilter]
            for i in identities:
                if i in f.identities:
                    return [f.whereFilter]
        
        # reject everything by default
        if has_filter:
            return ['1=0']
        return []
    
    async def get_field_permissions(self) -> dict[schema.FieldPermission, list[str]]:
        result: dict[schema.FieldPermission, list[str]] = {
            schema.FieldPermission.readOnly: [],
            schema.FieldPermission.readWrite: [],
            schema.FieldPermission.restricted: []
        }
        if not self.permissionFilters:
            return result
        
        identities = await get_permission_identities(self.request)
        perms = {}
        fields = self.Schema.model_fields.keys()
        for k in fields:
            perms[k] = self.defaultFieldPermission
        for f in self.permissionFilters:
            apply_filter = False
            if '*' in f.identities:
                apply_filter = True
            for i in identities:
                if i in f.identities:
                    apply_filter = True
            if apply_filter:
                for k in fields:
                    perms[k] = f.defaultFieldPermission
                    if k in (f.readWriteFields or []):
                        perms[k] = schema.FieldPermission.readWrite
                    if k in (f.readOnlyFields or []):
                        perms[k] = schema.FieldPermission.readOnly
                    if k in (f.restrictedFields or []):
                        perms[k] = schema.FieldPermission.restricted

        for k,v in perms.items():
            result[v].append(k)
        return result
 
    async def _transform_output_data(self, item: dict) -> dict:
        return item
    
    async def transform_output_data(self, item: pydantic.BaseModel) -> dict:
        field_permissions = await self.get_field_permissions()

        # delete protected fields
        protected_fields = (
            field_permissions[schema.FieldPermission.readOnly] + 
            field_permissions[schema.FieldPermission.restricted]
        )

        data = item.model_dump()
        for k in protected_fields:
            if k in data: del data[k]

        return await self._transform_output_data(data)

    async def _transform_create_data(self, item: dict) -> dict:
        return item
    
    async def transform_create_data(self, item: pydantic.BaseModel) -> dict:
        data = item.model_dump()
        data = await self._transform_create_data(data)
        field_permissions = await self.get_field_permissions()

        # delete protected fields
        protected_fields = (
            field_permissions[schema.FieldPermission.readOnly] + 
            field_permissions[schema.FieldPermission.restricted] + 
            ['id']
        )

        for k in protected_fields:
            if k in data: del data[k]
        userinfo = await get_userinfo(self.request)
        creator = None
        if userinfo:
            creator = userinfo.email
        data['creator'] = creator
        data['dateCreated'] = datetime.datetime.utcnow()
        data['dateModified'] = datetime.datetime.utcnow()
        return data

    async def _transform_update_data(self, item: dict) -> dict:
        return item
    
    async def transform_update_data(self, item: pydantic.BaseModel) -> dict:
        data = item.model_dump()
        data = await self._transform_update_data(data)
        field_permissions = await self.get_field_permissions()

        # delete protected fields
        protected_fields = (
            field_permissions[schema.FieldPermission.readOnly] + 
            field_permissions[schema.FieldPermission.restricted] + 
            ['id']
        )

        for k in protected_fields:
            if k in data: del data[k]

        userinfo = await get_userinfo(self.request)
        editor = None
        if userinfo:
            editor = userinfo.email
        data['editor'] = editor
        data['dateModified'] = datetime.datetime.utcnow()
        return data

    async def transform_delete_data(self, item):
        return item.model_dump()

    async def before_create(self, data: dict):
        pass

    async def after_create(self, item):
        pass

    async def before_update(self, data: dict):
        pass

    async def after_update(self, item):
        pass

    async def before_delete(self, item):
        pass

    async def after_delete(self, data):
        pass

    async def trigger(self, item, trigger, **kwargs):
        sm : StateMachine = self.StateMachine(self.request, item)
        return await sm.trigger(trigger, **kwargs)

    def model_validate(self, obj):
        return self.Schema.model_validate(obj)

