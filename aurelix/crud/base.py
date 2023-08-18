from transitions.extensions.asyncio import AsyncMachine
import dectate
from ..utils import validate_types
import pydantic
import fastapi
import datetime
from .. import exc
import typing

class StateMachine(object):

    field: str
    states: list[str]
    transitions: list[dict[str, str | list[str]]]

    def __init__(self, item):
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

class Collection(dectate.App):
    name: str
    Schema: type[pydantic.BaseModel]
    StateMachine: type[StateMachine]

    view = dectate.directive(ViewAction)

    @validate_types
    def __init__(self, request: fastapi.Request):
        self.request = request

    @classmethod
    def get_directive_methods(cls):
        # workaround with manual specification because this conflicts with pydantic
        yield 'view', cls.view
 

    @classmethod
    def routes(cls):
        dectate.commit(cls)
        views = cls.config.views
        collection_views = [v for k,v in views.items() if not v['path'].startswith('/{identifier}')]
        model_views = [v for k,v in views.items() if v['path'].startswith('/{identifier}')]
        return {
            'collection': sorted(collection_views, key=lambda v: len(v['path'])),
            'model': sorted(model_views, key=lambda v: len(v['path']))
        }
    


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
        sm = self.StateMachine(item)
        return await sm.trigger(trigger, **kwargs)

    def model_validate(self, obj):
        return self.Schema.model_validate(obj)

def get_collection(request:fastapi.Request, name: str) -> Collection: 
    return request.app.collection[name](request)

def get_schema(request: fastapi.Request, name: str) -> type[pydantic.BaseModel]:
    return request.app.collection[name].Schema

def get_collection_from_request(request: fastapi.Request):
    comps = request.url.path.split('/')
    if len(comps) < 2:
        raise exc.CollectionNotFoundException(request.url.path)
    collection_name = comps[1]
    if not collection_name in request.app.collection:
        raise exc.CollectionNotFoundException(request.url.path)
    return request.app.collection[collection_name](request)

Collection = typing.Annotated[Collection, fastapi.Depends(get_collection_from_request)]