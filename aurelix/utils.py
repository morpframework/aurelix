import pydantic
import enum
import fastapi
import typing
import functools

def validate_types(func):
    return pydantic.validate_call(config={'arbitrary_types_allowed': True})(func)

def snake_to_pascal(snake):
    return ''.join([k.capitalize() for k in snake.split('_')])

def snake_to_human(snake):
    return ' '.join([k.capitalize() for k in snake.split('_')])

def snake_to_camel(snake):
    return ''.join([k if i == 0 else k.capitalize() for i,k in enumerate(snake.split('_'))])

async def item_json(col, item: pydantic.BaseModel):
    return {
        'type': col.name, 
        'id': item.id,
        'attributes': await col.transform_output_data(item),
        'links': {
            'self': col.url(item),
            'collection': col.url()
        }}

P = typing.ParamSpec('P')
T = typing.TypeVar('T')

def copy_method_signature(source: typing.Callable[typing.Concatenate[typing.Any, P], T]) -> typing.Callable[[typing.Callable], typing.Callable[typing.Concatenate[typing.Any, P], T]]:
    def wrapper(target: typing.Callable) -> typing.Callable[typing.Concatenate[typing.Any, P], T]:
        @functools.wraps(source)
        def wrapped(self, *args: P.args, **kwargs: P.kwargs) -> T:
            return target(self, *args, **kwargs)

        return wrapped

    return wrapper
