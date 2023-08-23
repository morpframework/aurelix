# Configuration Options


## `aurelix.schema:AppSpec`



### `debug`

**Type:** `bool`

**Default Value:** `False`



### `title`

**Type:** `str`

**Default Value:** `Aurelix Application`



### `summary`

**Type:** `str | None`

**Default Value:** `None`



### `version`

**Type:** `str`

**Default Value:** `0.1.0`



### `docs_url`

**Type:** `str`

**Default Value:** `/`



### `redoc_url`

**Type:** `str | None`

**Default Value:** `None`



### `swagger_ui_oauth2_redirect_url`

**Type:** `str`

**Default Value:** `/oauth2-redirect`



### `swagger_ui_init_oauth`

**Type:** `aurelix.schema.InitOAuthSpec | None`

**Default Value:** `None`



### `terms_of_service`

**Type:** `str | None`

**Default Value:** `None`



### `model_directory`

**Description:** directory to load models from

**Type:** `str`

**Default Value:** `models`



### `libs_directory`

**Description:** directory to add into PYTHONPATH

**Type:** `str`

**Default Value:** `libs`



### `databases`

**Description:** list of databases

**Type:** `list[aurelix.schema.DatabaseSpec] | None`

**Default Value:** `None`



### `oidc_discovery_endpoint`

**Description:** OIDC discovery endpoint for authentication

**Type:** `str | None`

**Default Value:** `None`



### `views`

**Description:** List of views to register on this app

**Type:** `AppViewsSpec`

**Default Value:** `PydanticUndefined`


## `aurelix.schema:AppViewsSpec`



### `well_known_config`

**Type:** `ViewSpec`

**Default Value:** `PydanticUndefined`



### `extensions`

**Type:** `dict[str, aurelix.schema.ExtensionViewSpec] | None`

**Default Value:** `None`


## `aurelix.schema:ModelSpec`



### `name`

**Description:** Name of model

**Type:** `str`

**Default Value:** `PydanticUndefined`



### `storageType`

**Description:** Type of storage to store this model in

**Type:** `StorageTypeSpec`

**Default Value:** `PydanticUndefined`



### `fields`

**Description:** List of fields/properties this model have

**Type:** `dict[str, aurelix.schema.FieldSpec]`

**Default Value:** `PydanticUndefined`



### `objectStore`

**Description:** List of fields/properties that will be storing reference to uploaded files, and its upload method specification

**Type:** `dict[str, aurelix.schema.ObjectStoreSpec] | None`

**Default Value:** `None`



### `defaultFieldPermission`

**Description:** Default permission for fields

**Type:** `FieldPermission`

**Default Value:** `readWrite`



### `views`

**Description:** List of views this model have

**Type:** `ModelViewsSpec`

**Default Value:** `PydanticUndefined`



### `tags`

**Description:** OpenAPI tag which this model shall be tagged under

**Type:** `list[str] | None`

**Default Value:** `PydanticUndefined`



### `stateMachine`

**Description:** StateMachine specification for this model for workflow support

**Type:** `aurelix.schema.StateMachineSpec | None`

**Default Value:** `None`



### `beforeCreate`

**Description:** Event hook, before item is insert into database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### `afterCreate`

**Description:** Event hook, after item have been inserted into database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### `beforeUpdate`

**Description:** Event hook, before item is updated in database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### `afterUpdate`

**Description:** Event hook, after item is updated in database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### `beforeDelete`

**Description:** Event hook, before item deleted in database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### `afterDelete`

**Description:** Event hook, after item is deleted in database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### `transformCreateData`

**Description:** Transform hook, to transform item before inserted into database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### `transformUpdateData`

**Description:** Transform hook, to transform item before updated in database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### `transformOutputData`

**Description:** Transform hook, before item is returned for display

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### `permissionFilters`

**Description:** Permission rules for rows and field security

**Type:** `list[aurelix.schema.PermissionFilterSpec] | None`

**Default Value:** `None`



### `validators`

**Description:** Event hook, for validating model before insert/update into database

**Type:** `list[aurelix.schema.CodeRefSpec] | None`

**Default Value:** `None`



### `maxPageSize`

**Description:** Maximum number of items in listing pages

**Type:** `int`

**Default Value:** `100`


## `aurelix.schema:ModelViewsSpec`



### `listing`

**Type:** `ViewSpec`

**Default Value:** `PydanticUndefined`



### `create`

**Type:** `ViewSpec`

**Default Value:** `PydanticUndefined`



### `read`

**Type:** `ViewSpec`

**Default Value:** `PydanticUndefined`



### `update`

**Type:** `ViewSpec`

**Default Value:** `PydanticUndefined`



### `delete`

**Type:** `ViewSpec`

**Default Value:** `PydanticUndefined`



### `extensions`

**Type:** `dict[str, aurelix.schema.ExtensionViewSpec] | None`

**Default Value:** `None`


## `aurelix.schema:ViewSpec`



### `enabled`

**Type:** `bool`

**Default Value:** `True`


## `aurelix.schema:ExtensionViewSpec`



### `method`

**Description:** Request method of this view

**Type:** `RequestMethod`

**Default Value:** `GET`



### `summary`

**Description:** OpenAPI summary of this view

**Type:** `str | None`

**Default Value:** `None`



### `tags`

**Description:** OpenAPI tags for this view

**Type:** `list[str] | None`

**Default Value:** `PydanticUndefined`



### `openapi_extra`

**Type:** `dict[str, typing.Any] | None`

**Default Value:** `None`



### `handler`

**Description:** Function spec to handle this view

**Type:** `CodeRefSpec`

**Default Value:** `PydanticUndefined`


## `aurelix.schema:StorageTypeSpec`



### `name`

**Type:** `str`

**Default Value:** `PydanticUndefined`



### `database`

**Type:** `str`

**Default Value:** `PydanticUndefined`


## `aurelix.schema:StateMachineSpec`



### `initialState`

**Type:** `str`

**Default Value:** `PydanticUndefined`



### `field`

**Type:** `str`

**Default Value:** `workflowStatus`



### `states`

**Type:** `list[aurelix.schema.StateMachineStateSpec]`

**Default Value:** `PydanticUndefined`



### `transitions`

**Type:** `list[aurelix.schema.StateMachineTransitionSpec]`

**Default Value:** `PydanticUndefined`


## `aurelix.schema:DatabaseSpec`



### `name`

**Type:** `str`

**Default Value:** `PydanticUndefined`



### `url`

**Type:** `str`

**Default Value:** `PydanticUndefined`


## `aurelix.schema:CodeRefSpec`



### `function`

**Description:** Path to handler function in format app.module:function

**Type:** `str | None`

**Default Value:** `None`



### `code`

**Description:** Python code of handler function

**Type:** `str | None`

**Default Value:** `None`



### `function_name`

**Description:** Name of function to be loaded from code spec

**Type:** `str`

**Default Value:** `function`


