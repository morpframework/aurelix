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
    options: dict[str, typing.Any] | None = None
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
    method: RequestMethod = 'GET'
    summary: str | None = None
    tags: list[str] | None = pydantic.Field(default_factory=list)
    openapi_extra: dict[str, typing.Any] | None = None
    handler: CodeRefSpec

class ModelViewsSpec(pydantic.BaseModel):

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

class FieldPermission(enum.StrEnum):
    readOnly: str = "readOnly"
    readWrite: str = "readWrite"
    restricted: str = "restricted"

class PermissionFilterSpec(pydantic.BaseModel):
    identities: list[str]
    whereFilter: str | None = None
    defaultFieldPermission: FieldPermission = str(FieldPermission.readWrite) # default permission to apply on fields

    # field may appear in many list, the most restrictive wins
    readWriteFields: list[str] | None = None # fields listed here are readwrite
    readOnlyFields: list[str] | None = None # fields listed here are readonly
    restrictedFields: list[str] | None = None # fields listed here are hidden

class ModelSpec(pydantic.BaseModel):

    name: str
    storageType: StorageTypeSpec
    fields: dict[str, FieldSpec]
    defaultFieldPermission: FieldPermission = str(FieldPermission.readWrite)
    views: ModelViewsSpec = pydantic.Field(default_factory=ModelViewsSpec)
    tags: list[str] | None = pydantic.Field(default_factory=list)
    stateMachine: StateMachineSpec | None = None 
    beforeCreate: list[CodeRefSpec] | None = None
    afterCreate:  list[CodeRefSpec] | None = None
    beforeUpdate: list[CodeRefSpec] | None = None
    afterUpdate: list[CodeRefSpec] | None = None 
    beforeDelete: list[CodeRefSpec] | None = None
    afterDelete: list[CodeRefSpec] | None = None
    transformCreateData: list[CodeRefSpec] | None = None 
    transformUpdateData: list[CodeRefSpec] | None = None 
    transformOutputData: list[CodeRefSpec] | None = None
    permissionFilters: list[PermissionFilterSpec] | None = None
    maxPageSize: int = 100

class DatabaseSpec(pydantic.BaseModel):

    name: str
    url: str 

class InitOAuthSpec(pydantic.BaseModel):
    client_id: str 
    client_secret: str

class AppViewsSpec(pydantic.BaseModel):

    well_known_config: ViewSpec = pydantic.Field(default_factory=ViewSpec)
    extensions: dict[str, ExtensionViewSpec] | None = None

class AppSpec(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(protected_namespaces=())
    debug: bool = False
    title: str = "Aurelix Application"
    summary: str|None = None
    version: str = '0.1.0'
    docs_url: str = '/'
    redoc_url: str | None = None
    swagger_ui_oauth2_redirect_url: str = '/oauth2-redirect'
    swagger_ui_init_oauth: InitOAuthSpec | None = None
    terms_of_service: str | None = None
    model_directory: str = 'models'
    libs_directory: str = 'libs'
    databases: list[DatabaseSpec] | None = None
    oidc_discovery_endpoint: str | None = None
    views: AppViewsSpec = pydantic.Field(default_factory=AppViewsSpec)

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
    groups: list[str] | None = None

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
    stateMachine: WellKnownStateMachine | None = None
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