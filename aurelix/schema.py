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

class FieldTypeSpec(pydantic.BaseModel):
    type: str
    size: int | None = None
    enum: list[EnumSpec] | None = None
    sa_options: dict[str, object] | None = None

class FieldSpec(pydantic.BaseModel):
    title: str
    dataType: FieldTypeSpec
    required: bool = False
    default: typing.Any = None
    indexed: bool = False
    unique: bool = False
    foreignKey: str | None = None

class ViewSpec(pydantic.BaseModel):
    enabled: bool = True

class RequestMethod(enum.StrEnum):
    POST = 'POST'
    GET = 'GET'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'
    OPTIONS = 'OPTIONS'

class CodeRefSpec(pydantic.BaseModel):
    function: str | None = None
    code: str | None = None

class ExtensionViewSpec(pydantic.BaseModel):
    method: RequestMethod
    summary: str | None = None
    tags: list[str] | None = None
    openapi_extra: dict[str, typing.Any] | None = None
    handler: CodeRefSpec

class ViewsSpec(pydantic.BaseModel):

    listing: ViewSpec = pydantic.Field(default_factory=ViewSpec)
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
    onEnter: CodeRefSpec | None = None
    onExit: CodeRefSpec | None = None

class StateMachineSpec(pydantic.BaseModel):
    initialState: str
    field: str = 'workflowStatus'
    states: list[StateMachineStateSpec] 
    transitions: list[StateMachineTransitionSpec]

class ModelSpec(pydantic.BaseModel):

    name: str
    storageType: StorageTypeSpec
    fields: dict[str, FieldSpec]
    views: ViewsSpec = pydantic.Field(default_factory=ViewsSpec)
    tags: list[str]
    stateMachine: StateMachineSpec | None = None 
    beforeCreate: CodeRefSpec | None = None
    afterCreate: CodeRefSpec | None = None
    beforeUpdate: CodeRefSpec | None = None
    afterUpdate: CodeRefSpec | None = None 
    beforeDelete: CodeRefSpec | None = None
    afterDelete: CodeRefSpec | None = None
    transformCreateData: CodeRefSpec | None = None 
    transformUpdateData: CodeRefSpec | None = None 
    transformOutputData: CodeRefSpec | None = None

class DatabaseSpec(pydantic.BaseModel):

    name: str
    url: str 

class OAuth2Scheme(enum.StrEnum):
    PASSWORD = 'password'

class AppSpec(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(protected_namespaces=())

    debug: bool = False
    title: str = "Aether"
    summary: str|None = None
    version: str = '0.1.0'
    docs_url: str = '/'
    redoc_url: str | None = None
    swagger_ui_oauth2_redirect_url: str = '/oauth2-redirect'
    terms_of_service: str | None = None
    model_directory: str = 'models'
    libs_directory: str = 'libs'
    databases: list[DatabaseSpec] | None = None
    oauth2_scheme: OAuth2Scheme | None = None
    oidc_discovery_endpoint: str | None = None

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

class Token(pydantic.BaseModel):
    access_token: str 

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

class OIDCUserInfoResponse(pydantic.BaseModel):
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
    groups: list[str] | None = None