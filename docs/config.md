# Configuration Options


## AppSpec



### Field: AppSpec.debug

**Type:** `bool`

**Default Value:** `False`



### Field: AppSpec.title

**Type:** `str`

**Default Value:** `Aurelix Application`



### Field: AppSpec.summary

**Type:** `str | None`

**Default Value:** `None`



### Field: AppSpec.version

**Type:** `str`

**Default Value:** `0.1.0`



### Field: AppSpec.docs_url

**Type:** `str`

**Default Value:** `/`



### Field: AppSpec.redoc_url

**Type:** `str | None`

**Default Value:** `None`



### Field: AppSpec.swagger_ui_oauth2_redirect_url

**Type:** `str`

**Default Value:** `/oauth2-redirect`



### Field: AppSpec.swagger_ui_init_oauth

**Type:** `aurelix.schema.InitOAuthSpec | None`

**Default Value:** `None`



### Field: AppSpec.terms_of_service

**Type:** `str | None`

**Default Value:** `None`



### Field: AppSpec.model_directory

**Description:** directory to load models from

**Type:** `str`

**Default Value:** `models`



### Field: AppSpec.libs_directory

**Description:** directory to add into PYTHONPATH

**Type:** `str`

**Default Value:** `libs`



### Field: AppSpec.databases

**Description:** list of databases

**Type:** `list[aurelix.schema.DatabaseSpec] | None`

**Default Value:** `None`



### Field: AppSpec.oidc_discovery_endpoint

**Description:** OIDC discovery endpoint for authentication

**Type:** `str | None`

**Default Value:** `None`



### Field: AppSpec.views

**Description:** List of views to register on this app

**Type:** `AppViewsSpec`

**Default Value:** `PydanticUndefined`


## AppViewsSpec



### Field: AppViewsSpec.well_known_config

**Type:** `ViewSpec`

**Default Value:** `PydanticUndefined`



### Field: AppViewsSpec.extensions

**Type:** `dict[str, aurelix.schema.ExtensionViewSpec] | None`

**Default Value:** `None`


## ModelSpec



### Field: ModelSpec.name

**Description:** Name of model

**Type:** `str`

**Default Value:** `PydanticUndefined`



### Field: ModelSpec.storageType

**Description:** Type of storage to store this model in

**Type:** `StorageTypeSpec`

**Default Value:** `PydanticUndefined`



### Field: ModelSpec.fields

**Description:** List of fields/properties this model have

**Type:** `dict[str, aurelix.schema.FieldSpec]`

**Default Value:** `PydanticUndefined`



### Field: ModelSpec.defaultFieldPermission

**Description:** Default permission for fields

**Type:** `FieldPermission`

**Default Value:** `readWrite`



### Field: ModelSpec.views

**Description:** List of views this model have

**Type:** `ModelViewsSpec`

**Default Value:** `PydanticUndefined`



### Field: ModelSpec.tags

**Description:** OpenAPI tag which this model shall be tagged under

**Type:** `list[str] | None`

**Default Value:** `PydanticUndefined`



### Field: ModelSpec.stateMachine

**Description:** StateMachine specification for this model for workflow support

**Type:** `aurelix.schema.StateMachineSpec | None`

**Default Value:** `None`



### Field: ModelSpec.beforeCreate

**Description:** Event hook, before item is insert into database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### Field: ModelSpec.afterCreate

**Description:** Event hook, after item have been inserted into database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### Field: ModelSpec.beforeUpdate

**Description:** Event hook, before item is updated in database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### Field: ModelSpec.afterUpdate

**Description:** Event hook, after item is updated in database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### Field: ModelSpec.beforeDelete

**Description:** Event hook, before item deleted in database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### Field: ModelSpec.afterDelete

**Description:** Event hook, after item is deleted in database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### Field: ModelSpec.transformCreateData

**Description:** Transform hook, to transform item before inserted into database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### Field: ModelSpec.transformUpdateData

**Description:** Transform hook, to transform item before updated in database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### Field: ModelSpec.transformOutputData

**Description:** Transform hook, before item is returned for display

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### Field: ModelSpec.permissionFilters

**Description:** Permission rules for rows and field security

**Type:** `list[aurelix.schema.PermissionFilterSpec] | None`

**Default Value:** `None`



### Field: ModelSpec.validators

**Description:** Event hook, for validating model before insert/update into database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### Field: ModelSpec.maxPageSize

**Description:** Maximum number of items in listing pages

**Type:** `int`

**Default Value:** `100`


## ModelViewsSpec



### Field: ModelViewsSpec.listing

**Type:** `ViewSpec`

**Default Value:** `PydanticUndefined`



### Field: ModelViewsSpec.create

**Type:** `ViewSpec`

**Default Value:** `PydanticUndefined`



### Field: ModelViewsSpec.read

**Type:** `ViewSpec`

**Default Value:** `PydanticUndefined`



### Field: ModelViewsSpec.update

**Type:** `ViewSpec`

**Default Value:** `PydanticUndefined`



### Field: ModelViewsSpec.delete

**Type:** `ViewSpec`

**Default Value:** `PydanticUndefined`



### Field: ModelViewsSpec.extensions

**Type:** `dict[str, aurelix.schema.ExtensionViewSpec] | None`

**Default Value:** `None`


## ViewSpec



### Field: ViewSpec.enabled

**Type:** `bool`

**Default Value:** `True`


