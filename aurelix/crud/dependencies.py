import fastapi
import typing
from .. import exc
from .. import schema
from .base import BaseCollection

async def get_collection(request: fastapi.Request, name: str = None) -> BaseCollection:
    if name is None:
        comps = request.url.path.split('/')
        if len(comps) < 2:
            raise exc.CollectionNotFoundException(request.url.path)
        name = comps[1]
    if not name in request.app.collection:
        raise exc.CollectionNotFoundException(request.url.path)
    return request.app.collection[name](request)

async def _get_collection(request: fastapi.Request):
    return await get_collection(request)

Collection = typing.Annotated[BaseCollection, fastapi.Depends(_get_collection)]

async def get_model(request: fastapi.Request, collection: Collection):
    if not 'identifier' in request.path_params:
        raise exc.AurelixException(r'{identifier} parameter is required on this route to resolve model')
    identifier = request.path_params['identifier']
    if identifier.startswith('+'):
        raise exc.RecordNotFoundException(identifier)
    obj = await collection.get(identifier)
    if not obj:
        raise exc.RecordNotFoundException(identifier)
    return obj

Model = typing.Annotated[schema.CoreModel, fastapi.Depends(get_model)]
