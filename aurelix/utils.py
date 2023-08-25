import pydantic
import enum
import fastapi
import typing
import functools
from . import schema

def validate_types(func):
    return pydantic.validate_call(config={'arbitrary_types_allowed': True})(func)

def snake_to_pascal(snake):
    return ''.join([k.capitalize() for k in snake.split('_')])

def snake_to_human(snake):
    return ' '.join([k.capitalize() for k in snake.split('_')])

def snake_to_camel(snake):
    return ''.join([k if i == 0 else k.capitalize() for i,k in enumerate(snake.split('_'))])

async def item_json(col, item: pydantic.BaseModel):
    from .crud.dependencies import get_collection
    spec: schema.ModelSpec = col.spec
    request: fastapi.Request = col.request
    rels = {}
    for field_name, field in spec.fields.items():
        field_value = getattr(item, field_name)
        if field_value is None:
            continue
        if field.relation:
            rels.setdefault(field_name, {})
            field_col = await get_collection(request, field.relation.model)
            field_obj = await field_col.get(field_value)
            rels[field_name].setdefault('links', {})
            rels[field_name].setdefault('meta', {})
            rels[field_name]['data'] = await field_col.transform_output_data(field_obj)
            rels[field_name]['links']['self'] = field_col.url(field_obj)
            rels[field_name]['links']['collection'] = field_col.url()
            rels[field_name]['meta']['collection'] = field.relation.model
            rels[field_name]['meta']['identifier'] = str(field_col.get_identifier(field_obj))

    result = {
        'type': col.name, 
        'id': item.id,
        'attributes': await col.transform_output_data(item),
        'links': {
            'self': col.url(item),
            'collection': col.url()
        }}
    if rels:
        result['relationships'] = rels
    return result

P = typing.ParamSpec('P')
T = typing.TypeVar('T')

def copy_method_signature(source: typing.Callable[typing.Concatenate[typing.Any, P], T]) -> typing.Callable[[typing.Callable], typing.Callable[typing.Concatenate[typing.Any, P], T]]:
    def wrapper(target: typing.Callable) -> typing.Callable[typing.Concatenate[typing.Any, P], T]:
        @functools.wraps(source)
        def wrapped(self, *args: P.args, **kwargs: P.kwargs) -> T:
            return target(self, *args, **kwargs)

        return wrapped

    return wrapper
