from fastapi import FastAPI, Request, HTTPException, Body, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.exceptions import ValidationException
import json
import pydantic
import typing
import math
import enum
from .. import schema
from .. import exc
from .base import BaseCollection
from fastapi.responses import RedirectResponse
from ..dependencies import Token
from .dependencies import Model
from ..utils import snake_to_pascal, snake_to_human, item_json
from .. import state

class RelationshipMeta(pydantic.BaseModel):
    identifier: str 
    collection: str

def generate_relationship_model(name, app, collection_name):
    spec: schema.ModelSpec = state.APP_STATE[app]['models'][collection_name]
    attrs = {}
    for field_name, field in spec.fields.items():
        if field.relation:
            col: BaseCollection = state.APP_STATE[app]['model_collections'][field.relation.model]
            Schema = pydantic.create_model(snake_to_pascal(field.relation.model) + 'Links',
                data = (col.Schema, None),
                links = (schema.ModelResultLinks, None),
                meta = (RelationshipMeta, None)
            )
            attrs[field_name] = (typing.Optional[Schema], None)
    if not attrs:
        return None
    return pydantic.create_model(name, **attrs)

def register_collection(app, Collection: type[BaseCollection], create_enabled=True, read_enabled=True, 
                        update_enabled=True, delete_enabled=True, listing_enabled=True, upload_enabled=True,
                        download_enabled=True,
                        openapi_extra=None, max_page_size=100):

    openapi_extra = openapi_extra or {}
    collection_name = Collection.name
    Schema = Collection.Schema
    base_path = '/%s' % collection_name

    ModelRelation = generate_relationship_model(snake_to_pascal(collection_name) + 'ModelRelation', app, collection_name) 

    model_attrs = {
        'type': (str, None),
        'id': (int, None),
        'attributes': (Schema, None),
        'links': (typing.Optional[schema.ModelResultLinks], None)
    }

    if ModelRelation:
        model_attrs['relationships'] = (ModelRelation, None)

    ModelData = pydantic.create_model(
        snake_to_pascal(collection_name) + 'ModelData',
        **model_attrs
    )

    ModelSearchResult = pydantic.create_model(
        snake_to_pascal(collection_name) + 'ModelSearchResult', 
        data = (typing.List[ModelData], None),
        links = (typing.Optional[schema.SearchResultLinks], None),
        meta = (typing.Optional[schema.SearchResultMeta], None)
    )

    ModelResult = pydantic.create_model(
        snake_to_pascal(collection_name) + 'ModelResult', 
        data = (ModelData, None),
    )

    ModelInput = pydantic.create_model(
        Schema.__name__ + 'Input',
        **dict([(k,(v.annotation, v.default)) for k,v in Schema.model_fields.items() if k not in Model.model_fields.keys()])
    )

    ModelPatchInput = pydantic.create_model(
        Schema.__name__ + 'PatchInput',
         **dict([(k,(v.annotation | None, v.default)) for k,v in Schema.model_fields.items() if k not in Model.model_fields.keys()])       
    )

    if listing_enabled:
        @Collection.view('/', method='GET', openapi_extra=openapi_extra, 
                         summary='List %s' % snake_to_human(collection_name),
                         response_model_exclude_none=True)
        async def listing(request: Request, token: Token, query: str | None = None, 
                          page: int = 0, page_size: int = 10, order_by: str | None = None) -> ModelSearchResult:
            if page_size > max_page_size:
                page_size = 100
            if page_size < 1:
                page_size = 1
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
            self_url = endpoint_url + '?page=%s&page_size=%s' % (page, page_size)
            total_pages = int(math.ceil(float(total) / page_size))
            return {
                'data': [await item_json(col, i) for i in items],
                'links': {
                    'next': next,
                    'prev': prev,
                    'current': self_url,
                    'collection': endpoint_url
                },
                'meta': {
                    'total_records': total,
                    'total_pages': total_pages
                }
            }

    if create_enabled:
        @Collection.view('/', method='POST', openapi_extra=openapi_extra, summary='Create new %s' % snake_to_human(collection_name))
        async def create(request: Request, token: Token, item: ModelInput, 
                        response_model_exclude_none=True) -> ModelResult:
            col = Collection(request)
            item = await col.create(item)
            return ModelResult.model_validate({'data': await item_json(col, item)})

    if read_enabled:
        @Collection.view('/{identifier}', method='GET', openapi_extra=openapi_extra, 
                         summary='Get %s' % snake_to_human(collection_name),
                         response_model_exclude_none=True)
        async def read(request: Request, token: Token, col: Collection, model: Model, identifier: str) -> ModelResult:
            return ModelResult.model_validate({
                'data': await item_json(col, model)
            })

    if update_enabled:

        
        patch_example = json.dumps(ModelPatchInput().model_dump())
        
        @Collection.view('/{identifier}', method='PATCH', openapi_extra=openapi_extra, 
                         summary='Update %s' % snake_to_human(collection_name),
                         response_model_exclude_none=True)
        async def update_patch(request: Request, token: Token, identifier: str, col:Collection, 
                               patch: typing.Annotated[dict[str, typing.Any | None], Body(example=patch_example)]) -> ModelResult:
            try:
                ModelPatchInput.model_validate(patch)
            except pydantic.ValidationError as e:
                raise exc.ValidationError(e.errors())
            item = ModelPatchInput.model_validate(patch)
            item = await col.update(identifier, patch)
            return ModelResult.model_validate({'data': await item_json(col, item)})
        
        @Collection.view('/{identifier}', method='PUT', openapi_extra=openapi_extra, 
                         summary='Update %s (Full)' % snake_to_human(collection_name),
                         response_model_exclude_none=True)
        async def update(request: Request, token: Token, identifier: str, col:Collection, item: ModelInput) -> ModelResult:
            item = await col.update(identifier, item)
            return ModelResult.model_validate({'data': await item_json(col, item)})

    
    if delete_enabled:
        @Collection.view('/{identifier}', method='DELETE', openapi_extra=openapi_extra, summary='Delete %s' % snake_to_human(collection_name))
        async def delete(request: Request, token: Token, identifier: str, col: Collection, model: Model, confirmation: schema.DeleteConfirmation) -> schema.SimpleMessage:
            if confirmation.delete:
                result = await col.delete(identifier)
                return {
                    'detail': 'OK'
                }
            raise HTTPException(status_code=422, detail='Not Deleted')
        
    if upload_enabled and Collection.objectStore:
        @Collection.view('/{identifier}/file/{field}/+upload-url', method='GET', openapi_extra=openapi_extra, 
                        summary='Get presigned url to upload file to %s' % snake_to_human(collection_name))
        async def presigned_upload(request: Request, col: Collection, model: Model, 
                                   token: Token,
                                   identifier: str, field: str) -> schema.PresignedUrlResponse:
            url = await col.get_presigned_upload_url(identifier, field)
            return {
                'url': url
            }
    if download_enabled and Collection.objectStore: 
        @Collection.view('/{identifier}/file/{field}', method='GET', openapi_extra=openapi_extra, 
                        responses={
                            307: {
                                'description': 'Redirect to presigned url',
                            }
                        },
                        summary='Download file from %s' % snake_to_human(collection_name))
        async def download(request: Request, col: Collection, model: Model, 
                           token: Token,
                           identifier: str, field: str) -> RedirectResponse:
            url = await col.get_presigned_download_url(identifier, field)
            return RedirectResponse(url)
        

    if hasattr(Collection, 'StateMachine'):

        ModelTransition = pydantic.create_model(Schema.__name__ + 'Transition', 
            trigger=(enum.StrEnum('Trigger', [t['trigger'] for t in Collection.StateMachine.transitions]), None),
            data=(dict[str, typing.Any] | None, None)
        )
        @Collection.view('/{identifier}/+transition', method='POST', openapi_extra=openapi_extra, summary='Trigger state update for %s' % snake_to_human(collection_name))
        async def transition(request: Request, token: Token, identifier: str, col: Collection, model: Model, transition: ModelTransition) -> schema.SimpleMessage:
            await col.trigger(model, transition.trigger, data=transition.data)
            await col.update(identifier, model, modify_workflow_status=True)
            return {
                'detail': 'OK'
            }
        
    _routes = Collection.routes()
    collection_views = [v for v in _routes if not v['path'].startswith('/{identifier}')]
    model_views = [v for v in _routes if v['path'].startswith('/{identifier}')]

    for r in collection_views:
        path = base_path + r['path']
        getattr(app, r['method'])(path, **r['options'])(r['function'])

    for r in model_views:
        path = base_path + r['path']
        getattr(app, r['method'])(path, **r['options'])(r['function'])

    return app 

