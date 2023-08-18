import pydantic
import enum
import fastapi

def validate_types(func):
    return pydantic.validate_call(config={'arbitrary_types_allowed': True})(func)

class Tags(enum.Enum):
    datasource = 'Data Source Management'
    sourcecatalog = 'Source Dataset Catalog'
    profiling = 'Data Profiling'

def snake_to_pascal(snake):
    return ''.join([k.capitalize() for k in snake.split('_')])

def snake_to_human(snake):
    return ' '.join([k.capitalize() for k in snake.split('_')])

def snake_to_camel(snake):
    return ''.join([k.capitalize() for k in snake.split('_')])

async def item_json(col, item):
    return {
        'type': col.name, 
        'id': item.id,
        'attributes': await col.transform_output_data(item),
        'links': {
            'self': col.url(item)
        }}