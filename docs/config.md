# Configuration Options


## `aurelix.schema:AppSpec`



### Field: `debug`

**Type:** `bool`

**Default Value:** `False`



### Field: `title`

**Type:** `str`

**Default Value:** `Aurelix Application`



### Field: `summary`

**Type:** `str | None`

**Default Value:** `None`



### Field: `version`

**Type:** `str`

**Default Value:** `0.1.0`



### Field: `docs_url`

**Type:** `str`

**Default Value:** `/`



### Field: `redoc_url`

**Type:** `str | None`

**Default Value:** `None`



### Field: `swagger_ui_oauth2_redirect_url`

**Type:** `str`

**Default Value:** `/oauth2-redirect`



### Field: `swagger_ui_init_oauth`

**Type:** `aurelix.schema.InitOAuthSpec | None`

**Default Value:** `None`



### Field: `terms_of_service`

**Type:** `str | None`

**Default Value:** `None`



### Field: `model_directory`

**Description:** directory to load models from

**Type:** `str`

**Default Value:** `models`



### Field: `libs_directory`

**Description:** directory to add into PYTHONPATH

**Type:** `str`

**Default Value:** `libs`



### Field: `databases`

**Description:** list of databases

**Type:** `list[aurelix.schema.DatabaseSpec] | None`

**Default Value:** `None`



### Field: `oidc_discovery_endpoint`

**Description:** OIDC discovery endpoint for authentication

**Type:** `str | None`

**Default Value:** `None`



### Field: `views`

**Description:** List of views to register on this app

**Type:** `AppViewsSpec`

**Default Value:** `PydanticUndefined`


## `aurelix.schema:AppViewsSpec`



### Field: `well_known_config`

**Type:** `ViewSpec`

**Default Value:** `PydanticUndefined`



### Field: `extensions`

**Type:** `dict[str, aurelix.schema.ExtensionViewSpec] | None`

**Default Value:** `None`


## `aurelix.schema:ModelSpec`



### Field: `name`

**Description:** Name of model

**Type:** `str`

**Default Value:** `PydanticUndefined`



### Field: `storageType`

**Description:** Type of storage to store this model in

**Type:** `StorageTypeSpec`

**Default Value:** `PydanticUndefined`



### Field: `fields`

**Description:** List of fields/properties this model have

**Type:** `dict[str, aurelix.schema.FieldSpec]`

**Default Value:** `PydanticUndefined`



### Field: `defaultFieldPermission`

**Description:** Default permission for fields

**Type:** `FieldPermission`

**Default Value:** `readWrite`



### Field: `views`

**Description:** List of views this model have

**Type:** `ModelViewsSpec`

**Default Value:** `PydanticUndefined`



### Field: `tags`

**Description:** OpenAPI tag which this model shall be tagged under

**Type:** `list[str] | None`

**Default Value:** `PydanticUndefined`



### Field: `stateMachine`

**Description:** StateMachine specification for this model for workflow support

**Type:** `aurelix.schema.StateMachineSpec | None`

**Default Value:** `None`



### Field: `beforeCreate`

**Description:** Event hook, before item is insert into database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### Field: `afterCreate`

**Description:** Event hook, after item have been inserted into database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### Field: `beforeUpdate`

**Description:** Event hook, before item is updated in database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### Field: `afterUpdate`

**Description:** Event hook, after item is updated in database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### Field: `beforeDelete`

**Description:** Event hook, before item deleted in database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### Field: `afterDelete`

**Description:** Event hook, after item is deleted in database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### Field: `transformCreateData`

**Description:** Transform hook, to transform item before inserted into database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### Field: `transformUpdateData`

**Description:** Transform hook, to transform item before updated in database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### Field: `transformOutputData`

**Description:** Transform hook, before item is returned for display

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### Field: `permissionFilters`

**Description:** Permission rules for rows and field security

**Type:** `list[aurelix.schema.PermissionFilterSpec] | None`

**Default Value:** `None`



### Field: `validators`

**Description:** Event hook, for validating model before insert/update into database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### Field: `maxPageSize`

**Description:** Maximum number of items in listing pages

**Type:** `int`

**Default Value:** `100`


## `aurelix.schema:ModelViewsSpec`



### Field: `listing`

**Type:** `ViewSpec`

**Default Value:** `PydanticUndefined`



### Field: `create`

**Type:** `ViewSpec`

**Default Value:** `PydanticUndefined`



### Field: `read`

**Type:** `ViewSpec`

**Default Value:** `PydanticUndefined`



### Field: `update`

**Type:** `ViewSpec`

**Default Value:** `PydanticUndefined`



### Field: `delete`

**Type:** `ViewSpec`

**Default Value:** `PydanticUndefined`



### Field: `extensions`

**Type:** `dict[str, aurelix.schema.ExtensionViewSpec] | None`

**Default Value:** `None`


## `aurelix.schema:ViewSpec`



### Field: `enabled`

**Type:** `bool`

**Default Value:** `True`


