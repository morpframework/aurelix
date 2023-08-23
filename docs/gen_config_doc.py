from aurelix import schema
import pydantic
import typing
import types

def gendoc(Model: pydantic.BaseModel) -> str:
        result = [
            '# Configuration Options'
        ]
        model_name = Model.__name__
        result.append('## %s' % Model.__name__)
        if Model.__doc__ != pydantic.BaseModel.__doc__:
            result.append(Model.__doc__ or '')
        anno = Model.__annotations__
        for field_name, field in Model.model_fields.items():
            dtype = anno[field_name]
            if isinstance(dtype, types.UnionType) or isinstance(dtype, types.GenericAlias):
                ftype = str(dtype)
            elif issubclass(dtype, pydantic.BaseModel):
                ftype = dtype.__name__
            elif hasattr(dtype, '__name__'):
                ftype = dtype.__name__
            else:
                ftype = str(dtype)
            result.append('### Field: %s.%s' % (model_name, field_name))
            result.append('**Type:** ' + str(ftype))
            result.append('**Default Value:** ' + str(field.default))
            if field.description:
                result.append('**Description:** ' + (field.description or ''))
            result.append('')
        print('\n\n'.join(result))


gendoc(schema.AppSpec)
gendoc(schema.AppViewsSpec)
gendoc(schema.ModelSpec)
gendoc(schema.ModelViewsSpec)
gendoc(schema.ViewSpec)
