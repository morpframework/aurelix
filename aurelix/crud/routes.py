from fastapi import FastAPI, Request, HTTPException
import pydantic
import typing
import math
from fastapi.responses import RedirectResponse
from ..db.model import CoreModel
from ..utils import snake_to_pascal, snake_to_human, item_json

class SearchResultLinks(pydantic.BaseModel):
    next: str | None = None
    prev: str | None = None

class SearchResultMeta(pydantic.BaseModel):
    total_records: int | None = None
    total_pages: int | None = None

class SearchResult(pydantic.BaseModel):
    data: list[pydantic.BaseModel]

class ModelResultLinks(pydantic.BaseModel):
    self: str | None = None

class DeleteConfirmation(pydantic.BaseModel):
    delete: bool = False

class SimpleMessage(pydantic.BaseModel):
    detail: str | dict | None = None


def register_collection(app, Collection, create_enabled=True, read_enabled=True, 
                        update_enabled=True, delete_enabled=True, listing_enabled=True, 
                        openapi_extra=None):
    
    openapi_extra = openapi_extra or {}
    collection_name = Collection.name
    Schema = Collection.Schema
    base_path = '/%s' % collection_name


    ModelData = pydantic.create_model(
        snake_to_pascal(collection_name) + 'ModelData',
        type = (str, None),
        id = (int, None),
        attributes = (Schema, None),
        links = (typing.Optional[ModelResultLinks], None)
    )

    ModelSearchResult = pydantic.create_model(
        snake_to_pascal(collection_name) + 'ModelSearchResult', 
        data = (typing.List[ModelData], None),
        links = (typing.Optional[SearchResultLinks], None),
        meta = (typing.Optional[SearchResultMeta], None)
    )

    ModelResult = pydantic.create_model(
        snake_to_pascal(collection_name) + 'ModelResult', 
        data = (ModelData, None),
    )

    ModelInput = pydantic.create_model(
        Schema.__name__ + 'Input',
        **dict([(k,(v.annotation, v.default)) for k,v in Schema.model_fields.items() if k not in CoreModel.model_fields.keys()])
    )


    if listing_enabled:
        @Collection.view('/', method='GET', openapi_extra=openapi_extra, summary='List %s' % snake_to_human(collection_name))
        async def listing(request: Request, query: str | None = None, 
                          page: int = 0, page_size: int = 10, order_by: str | None = None) -> ModelSearchResult:
            col = Collection(request)
            if order_by:
                order_by = [o.split(':') for o in order_by.strip().replace(',',' ').split(' ')]
            total = await col.count(query=query)
            items = await col.search(query=query, offset=page * page_size, limit=page_size, order_by=order_by)
            endpoint_url = col.url()
            next = None
            if (total - (page*page_size)) > page_size:
                next = endpoint_url + '?page=%s&page_size=%s' % (page + 1, page_size)
            if page <= 0:
                prev = None
            else:
                prev = endpoint_url + '?page=%s&page_size=%s' % (page - 1, page_size)

            total_pages = int(math.ceil(float(total) / page_size))
            return {
                'data': [await item_json(col, i) for i in items],
                'links': {
                    'next': next,
                    'prev': prev
                },
                'meta': {
                    'total_records': total,
                    'total_pages': total_pages
                }
            }

    if create_enabled:
        @Collection.view('/', method='POST', openapi_extra=openapi_extra, summary='Create new %s' % snake_to_human(collection_name))
        async def create(request: Request, item: ModelInput) -> ModelResult:
            col = Collection(request)
            item = await col.create(item)
            return ModelResult.model_validate({'data': await item_json(col, item)})

    if read_enabled:
        @Collection.view('/{identifier}', method='GET', openapi_extra=openapi_extra, summary='Get %s' % snake_to_human(collection_name))
        async def read(request: Request, identifier: str) -> ModelResult:
            if identifier.startswith('+'):
                raise HTTPException(status_code=404, detail='Not Found')
            col = Collection(request)
            item = await col.get(identifier)
            if item == None:
                raise HTTPException(status_code=404, detail='Not Found')
            return ModelResult.model_validate({
                'data': await item_json(col, item)
            })

    if update_enabled:
        @Collection.view('/{identifier}', method='PUT', openapi_extra=openapi_extra, summary='Update %s' % snake_to_human(collection_name))
        async def update(request: Request, identifier: str, item: ModelInput) -> ModelResult:
            if identifier.startswith('+'):
                raise HTTPException(status_code=404, detail='Not Found')
            exist = await Collection(request).get(identifier)
            if exist == None:
                raise HTTPException(status_code=404, detail='Not Found')
            col = Collection(request)
            item = await col.update(identifier, item)
            return ModelResult.model_validate({'data': await item_json(col, item)})
    
    if delete_enabled:
        @Collection.view('/{identifier}', method='DELETE', openapi_extra=openapi_extra, summary='Delete %s' % snake_to_human(collection_name))
        async def delete(request: Request, identifier: str, confirmation: DeleteConfirmation) -> SimpleMessage:
            if identifier.startswith('+'):
                raise HTTPException(status_code=404, detail='Not Found')
            col = Collection(request)
            item = await col.get(identifier)
            if item == None:
                raise HTTPException(status_code=404, detail='Not Found')
            if confirmation.delete:
                result = await col.delete(identifier)
                return {
                    'detail': 'OK'
                }
            raise HTTPException(status_code=422, detail='Not Deleted')
        
    if hasattr(Collection, 'StateMachine'):

        ModelTransition = pydantic.create_model(Schema.__name__ + 'Transition', 
            trigger=(str, None),
            data=(dict[str, typing.Any] | None, None)
        )
        @Collection.view('/{identifier}/+transition', method='POST', openapi_extra=openapi_extra, summary='Trigger state update for %s' % snake_to_human(collection_name))
        async def transition(request: Request, identifier: str, transition: ModelTransition):
            if identifier.startswith('+'):
                raise HTTPException(status_code=404, detail='Not Found')
            col = Collection(request)
            item = await col.get(identifier)
            if item == None:
                raise HTTPException(status_code=404, detail='Not Found')
            await col.trigger(item, transition.trigger, data=transition.data)
            await col.update(identifier, item)
            return {
                'detail': 'OK'
            }
        
    _routes = Collection.routes()
    for r in _routes['collection']:
        path = base_path + r['path']
        getattr(app, r['method'])(path, **r['options'])(r['function'])


    for r in _routes['model']:
        path = base_path + r['path']
        getattr(app, r['method'])(path, **r['options'])(r['function'])

    return app 

