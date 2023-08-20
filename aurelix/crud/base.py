from transitions.extensions.asyncio import AsyncMachine
import dectate
from ..utils import validate_types
import pydantic
import fastapi
import datetime
from .. import exc
from ..dependencies import get_userinfo
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

    async def transform_output_data(self, item):
        return item

    async def _transform_create_data(self, item):
        return item.model_dump()
    
    async def transform_create_data(self, item):
        data = await self._transform_create_data(item)
        # delete protected fields
        for k in ['id']:
            if k in data: del data[k]
        userinfo = await get_userinfo(self.request)
        creator = None
        if userinfo:
            creator = userinfo.email
        data['creator'] = creator
        data['dateCreated'] = datetime.datetime.utcnow()
        data['dateModified'] = datetime.datetime.utcnow()
        return data

    async def _transform_update_data(self, item):
        return item.model_dump()
    
    async def transform_update_data(self, item):
        data = await self._transform_update_data(item)
        # delete protected fields
        for k in ['id']:
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

