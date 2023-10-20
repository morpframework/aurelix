import pydantic
import enum
import datetime
import typing

class CoreModel(pydantic.BaseModel):
    id: int | None = None
    dateCreated: datetime.datetime | None = None
    dateModified: datetime.datetime | None = None
    creator: str | None = None
    editor: str | None = None

class StorageTypeSpec(pydantic.BaseModel):
    name: str
    database: str

class EnumSpec(pydantic.BaseModel):
    value: str
    label: str

class CodeRefSpec(pydantic.BaseModel):
    function: str | None = pydantic.Field(None, description='Path to handler function in format app.module:function')
    code: str | None = pydantic.Field(None, description='Python code of handler function')
    function_name: str = pydantic.Field('function', description='Name of function to be loaded from code spec')

class FieldTypeSpec(pydantic.BaseModel):
    type: str
    size: int | None = None
    enum: list[EnumSpec] | None = None
    options: dict[str, typing.Any] | None = None
    sa_options: dict[str, object] | None = None

class FieldRelationSpec(pydantic.BaseModel):
    model: str
    field: str
    constraint: bool = True

class FieldSpec(pydantic.BaseModel):
    title: str
    dataType: FieldTypeSpec = pydantic.Field(validation_alias=pydantic.AliasChoices('data_type', 'dataType'))
    required: bool = False
    default: typing.Any = None
    indexed: bool = False
    unique: bool = False
    relation: FieldRelationSpec | None = None
    validators: list[CodeRefSpec] | None = None
    inputTransformers: list[CodeRefSpec] | None = pydantic.Field(None,
                                                                 validation_alias=pydantic.AliasChoices('input_transformers', 'inputTransformers'))
    outputTransformers: list[CodeRefSpec] | None = pydantic.Field(None,
                                                                 validation_alias=pydantic.AliasChoices('output_transformers', 'outputTransformers'))



class ViewSpec(pydantic.BaseModel):
    enabled: bool = True

class RequestMethod(enum.StrEnum):
    POST = 'POST'
    GET = 'GET'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'
    OPTIONS = 'OPTIONS'


class ExtensionViewSpec(pydantic.BaseModel):
    method: RequestMethod = pydantic.Field('GET', description='Request method of this view')
    summary: str | None = pydantic.Field(None, description='OpenAPI summary of this view')
    tags: list[str] | None = pydantic.Field(default_factory=list, description='OpenAPI tags for this view')
    openapi_extra: dict[str, typing.Any] | None = None
    handler: CodeRefSpec = pydantic.Field(description='Function spec to handle this view')

class ListingViewSpec(ViewSpec):
    maxPageSize: int = pydantic.Field(100, description='Maximum number of items in listing pages',
                                    validation_alias=pydantic.AliasChoices('max_page_size', 'maxPageSize'))

class ModelViewsSpec(pydantic.BaseModel):

    listing: ListingViewSpec = pydantic.Field(default_factory=ListingViewSpec)
    create: ViewSpec = pydantic.Field(default_factory=ViewSpec)
    read: ViewSpec = pydantic.Field(default_factory=ViewSpec)
    update: ViewSpec = pydantic.Field(default_factory=ViewSpec)
    delete: ViewSpec = pydantic.Field(default_factory=ViewSpec)
    extensions: dict[str, ExtensionViewSpec] | None = None

class StateMachineStateSpec(pydantic.BaseModel):
    value: str
    label: str

class StateMachineTransitionSpec(pydantic.BaseModel):
    trigger: str 
    label: str 
    source: str | list[str]
    dest: str
    onEnter: CodeRefSpec | None = pydantic.Field(None, validation_alias=pydantic.AliasChoices('on_enter', 'onEnter'))
    onExit: CodeRefSpec | None = pydantic.Field(None, validation_alias=pydantic.AliasChoices('on_exit', 'onExit'))


class StateMachineSpec(pydantic.BaseModel):
    initialState: str = pydantic.Field(
        validation_alias=pydantic.AliasChoices('initial_state', 'initialState'))
    field: str = 'workflowStatus'
    states: list[StateMachineStateSpec] 
    transitions: list[StateMachineTransitionSpec]

class FieldPermission(enum.StrEnum):
    readOnly: str = "readOnly"
    readWrite: str = "readWrite"
    restricted: str = "restricted"

class PermissionFilterSpec(pydantic.BaseModel):
    identities: list[str] = pydantic.Field(description='List of identities to match against')
    whereFilter: str | None = pydantic.Field(None, description="'where' statement to add to CRUD uperations if identity matches",
                                            validation_alias=pydantic.AliasChoices('where_filter', 'whereFilter'))
    defaultFieldPermission: FieldPermission = pydantic.Field(str(FieldPermission.readWrite), 
                                                description='Default permission for fields',
                                                validation_alias=pydantic.AliasChoices('default_field_permission', 'defaultFieldPermmission'))

    # field may appear in many list, the most restrictive wins
    readWriteFields: list[str] | None = pydantic.Field(None, description='List of fields that are read-write',
                                                       validation_alias=pydantic.AliasChoices('read_write_fields', 'readWriteFields'))
    readOnlyFields: list[str] | None = pydantic.Field(None, description='List of fields that are read-only',
                                                      validation_alias=pydantic.AliasChoices('read_only_fields', 'readOnlyFields'))
    restrictedFields: list[str] | None = pydantic.Field(None, description='List of fields that are hidden/restricted',
                                                    validation_alias=pydantic.AliasChoices('restricted_field', 'restrictedFields'))

class ObjectStoreType(enum.StrEnum):
    minio: str = 'minio'

class ObjectStoreSpec(pydantic.BaseModel):

    name: str
    type: ObjectStoreType = str(ObjectStoreType.minio)
    endpoint_url: str | None = None
    endpoint_url_env: str | None =None
    access_key_env: str | None = None
    secret_key_env: str | None = None
    access_key: str | None = None
    secret_key: str | None = None


    @pydantic.model_validator(mode='before')
    @classmethod
    def _validate(cls,data):
        if ((not (data.get('access_key_env') or data.get('access_key'))) or
            data.get('access_key_env') and data.get('access_key')
            ):
            raise ValueError("Either access_key or access_key_env is required")
        if ((not (data.get('secret_key_env') or data.get('secret_key'))) or
            data.get('secret_key_env') and data.get('secret_key')
            ):
            raise ValueError("Either secret_key or secret_key_env is required")
        if ((not (data.get('endpoint_url_env') or data.get('endpoint_url'))) or
            data.get('endpoint_url_env') and data.get('endpoint_url')
            ):
            raise ValueError("Either endpoint_url or endpoint_url_env is required")
        return data
        


class FieldObjectStoreSpec(pydantic.BaseModel):

    objectStore: str = pydantic.Field(validation_alias=pydantic.AliasChoices('object_store', 'objectStore'))
    bucket: str

class ModelSpec(pydantic.BaseModel):

    spec_version: str = 'model/0.1'
    name: str = pydantic.Field(description='Name of model')
    storageType: StorageTypeSpec = pydantic.Field(description='Type of storage to store this model in',
            validation_alias=pydantic.AliasChoices('storage_type', 'storageType'))
    fields: dict[str, FieldSpec] = pydantic.Field(description='List of fields/properties this model have')
    objectStore: dict[str, FieldObjectStoreSpec] | None = pydantic.Field(None,
        description='List of fields/properties that will be storing reference to uploaded files, and its upload method specification',
        validation_alias=pydantic.AliasChoices('object_store', 'objectStore'))
    defaultFieldPermission: FieldPermission = pydantic.Field(str(FieldPermission.readWrite), description='Default permission for fields',
        validation_alias=pydantic.AliasChoices('defaultFieldPermission', 'default_field_permission'))
    views: ModelViewsSpec = pydantic.Field(default_factory=ModelViewsSpec, description='List of views this model have')
    tags: list[str] | None = pydantic.Field(default_factory=list, description='OpenAPI tag which this model shall be tagged under')
    stateMachine: StateMachineSpec | None = pydantic.Field(None, description='StateMachine specification for this model for workflow support',
        validation_alias=pydantic.AliasChoices('state_machine', 'stateMachine'))
    beforeCreate: list[CodeRefSpec] | None = pydantic.Field(None, description='Event hook, before item is insert into database',
        validation_alias=pydantic.AliasChoices('before_create', 'beforeCreate'))
    afterCreate:  list[CodeRefSpec] | None = pydantic.Field(None, description='Event hook, after item have been inserted into database',
        validation_alias=pydantic.AliasChoices('after_create', 'afterCreate'))
    beforeUpdate: list[CodeRefSpec] | None = pydantic.Field(None, description='Event hook, before item is updated in database',
        validation_alias=pydantic.AliasChoices('before_update', 'beforeUpdate'))
    afterUpdate: list[CodeRefSpec] | None = pydantic.Field(None, description='Event hook, after item is updated in database',
        validation_alias=pydantic.AliasChoices('after_update', 'afterUpdate'))
    beforeDelete: list[CodeRefSpec] | None = pydantic.Field(None, description='Event hook, before item deleted in database',
        validation_alias=pydantic.AliasChoices('before_delete', 'beforeDelete'))
    afterDelete: list[CodeRefSpec] | None = pydantic.Field(None, description='Event hook, after item is deleted in database',
        validation_alias=pydantic.AliasChoices('after_delete', 'afterDelete'))
    transformCreateData: list[CodeRefSpec] | None = pydantic.Field(None, description='Transform hook, to transform item before inserted into database',
        validation_alias=pydantic.AliasChoices('transform_create_data', 'transformCreateData'))
    transformUpdateData: list[CodeRefSpec] | None = pydantic.Field(None, description='Transform hook, to transform item before updated in database',
        validation_alias=pydantic.AliasChoices('transform_update_data', 'transformUpdateData'))
    transformOutputData: list[CodeRefSpec] | None = pydantic.Field(None, description='Transform hook, before item is returned for display',
        validation_alias=pydantic.AliasChoices('transform_output_data', 'transformOutputData'))
    permissionFilters: list[PermissionFilterSpec] | None = pydantic.Field(None, description='Permission rules for rows and field security',
        validation_alias=pydantic.AliasChoices('permission_filters', 'permissionFilters'))
    validators: list[CodeRefSpec] | None = pydantic.Field(None, description='Event hook, for validating model before insert/update into database')


class DatabaseType(enum.StrEnum):

    sqlalchemy: str= 'sqlalchemy'

class DatabaseSpec(pydantic.BaseModel):

    name: str
    type: DatabaseType = str(DatabaseType.sqlalchemy)
    auto_initialize: bool = False
    url: str | None = None
    url_env: str | None = None

    @pydantic.model_validator(mode='before')
    @classmethod
    def _validate(cls, data):
        if ((not (data.get('url_env') or data.get('url'))) or
            data.get('url_env') and data.get('url')
            ):
            raise ValueError("Either url or url_env is required")
        return data

class InitOAuthSpec(pydantic.BaseModel):
    client_id: str 
    client_secret: str

class AppViewsSpec(pydantic.BaseModel):

    well_known_config: ViewSpec = pydantic.Field(default_factory=ViewSpec)
    extensions: dict[str, ExtensionViewSpec] | None = None

class AppSpec(pydantic.BaseModel):

    spec_version: str = 'app/0.1'
    model_config = pydantic.ConfigDict(protected_namespaces=())
    debug: bool = False
    # following config are just delegating to fastapi.FastAPI constructor
    title: str = "Aurelix Application"
    summary: str|None = None
    version: str = '0.1.0'
    docs_url: str = '/'
    redoc_url: str | None = None
    swagger_ui_oauth2_redirect_url: str = '/oauth2-redirect'
    swagger_ui_init_oauth: InitOAuthSpec | None = None
    terms_of_service: str | None = None

    # following config are aurelix
    model_directory: str = pydantic.Field('models', description='directory to load models from')
    libs_directory: str = pydantic.Field('libs', description='directory to add into PYTHONPATH')

    # list of sqlalchemy databases
    databases: list[DatabaseSpec] | None = pydantic.Field(None, description='list of databases')
    objectStores: list[ObjectStoreSpec] | None = pydantic.Field(None,
        description='list of object stores', validation_alias=pydantic.AliasChoices('object_stores', 'objectStores'))
    oidc_discovery_endpoint: str | None = pydantic.Field(None, description='OIDC discovery endpoint for authentication')
    views: AppViewsSpec = pydantic.Field(default_factory=AppViewsSpec, description='List of views to register on this app')

class SearchResultLinks(pydantic.BaseModel):
    next: str | None = None
    prev: str | None = None
    current: str | None = None
    collection: str | None = None

class SearchResultMeta(pydantic.BaseModel):
    total_records: int | None = None
    total_pages: int | None = None

class SearchResult(pydantic.BaseModel):
    data: list[pydantic.BaseModel]

class ModelResultLinks(pydantic.BaseModel):
    self: str | None = None
    collection: str | None = None

class DeleteConfirmation(pydantic.BaseModel):
    delete: bool = False

class SimpleMessage(pydantic.BaseModel):
    detail: str | dict | None = None

class User(pydantic.BaseModel):
    pass

class OIDCConfiguration(pydantic.BaseModel):
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    jwks_uri: str
    response_types_supported: list[str]
    subject_types_supported: list[str]
    id_token_signing_alg_values_supported: list[str]
    scopes_supported: list[str]
    token_endpoint_auth_methods_supported: list[str]
    claims_supported: list[str]


class OIDCAddress(pydantic.BaseModel):
    formatted: str | None = None
    street_address: str | None = None
    locality: str | None = None
    region: str | None = None
    postal_code: str | None = None
    country: str | None = None

class OIDCUserInfo(pydantic.BaseModel):
    sub: str
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    middle_name: str | None = None
    nickname: str | None = None
    preferred_username: str | None = None
    profile: str | None = None
    picture: str | None = None
    website: str | None = None
    email: str 
    email_verified: bool | None = None
    gender: str | None = None
    birthdate: str | None = None
    zoneinfo: str | None = None
    locale: str | None = None
    phone_number: str | None = None
    phone_number_verified: bool | None = None
    address: OIDCAddress | None = None
    updated_at: int | None = None
    roles: list[str] | None = pydantic.Field(None, validation_alias=pydantic.AliasChoices('groups','roles'))

class RealmAccess(pydantic.BaseModel):
    roles: list[str] | None

class ResourceAccess(pydantic.BaseModel):
    roles: list[str] | None

class OIDCAccessToken(pydantic.BaseModel):
    exp: int | None = None
    iat: int | None = None
    jti: str | None = None
    iss: str | None = None
    aud: str | None = None
    sub: str | None = None
    typ: str | None = None
    azp: str | None = None
    session_state: str | None = None
    acr: str | None = None
    allowed_origins: list[str] | None = None
    realm_access: RealmAccess | None = None
    resource_access: dict[str, ResourceAccess] | None = None
    scope: str | None = None
    sid: str | None = None
    email_verified: bool | None = None
    roles: list[str] | None = pydantic.Field(None, validation_alias=pydantic.AliasChoices('roles','groups'))
    name: str | None = None
    preferred_username: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    email: str | None = None


class WellKnownStateMachineTrigger(pydantic.BaseModel):
    name: str
    label: str
    source: str | list[str]

class WellKnownStateMachineStates(pydantic.BaseModel):
    name: str
    label: str

class WellKnownStateMachine(pydantic.BaseModel):
    triggers: list[WellKnownStateMachineTrigger]
    states: list[WellKnownStateMachineStates]
    field: str

class WellKnownCollection(pydantic.BaseModel):
    name: str
    jsonSchema: dict = pydantic.Field(alias='schema')
    stateMachine: WellKnownStateMachine | None = pydantic.Field(None,
        validation_alias=pydantic.AliasChoices('state_machine', 'stateMachine')
    )
    links: dict[str, str]

class WellKnownConfiguration(pydantic.BaseModel):

    collections: dict[str, WellKnownCollection]
    openid_configuration: OIDCConfiguration | None = pydantic.Field(default=None, alias='openid-configuration')

class OIDCTokenResponse(pydantic.BaseModel):
    access_token: str | None = None
    token_type: str | None = None
    expires_in: int | None = None
    refresh_token: str | None = None
    id_token: str | None = None

class PresignedUrlResponse(pydantic.BaseModel):
    url: str
