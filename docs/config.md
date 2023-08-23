# Configuration Options

## AppSpec



### Field: AppSpec.debug

**Type:** bool

**Default Value:** False



### Field: AppSpec.title

**Type:** str

**Default Value:** Aurelix Application



### Field: AppSpec.summary

**Type:** str | None

**Default Value:** None



### Field: AppSpec.version

**Type:** str

**Default Value:** 0.1.0



### Field: AppSpec.docs_url

**Type:** str

**Default Value:** /



### Field: AppSpec.redoc_url

**Type:** str | None

**Default Value:** None



### Field: AppSpec.swagger_ui_oauth2_redirect_url

**Type:** str

**Default Value:** /oauth2-redirect



### Field: AppSpec.swagger_ui_init_oauth

**Type:** aurelix.schema.InitOAuthSpec | None

**Default Value:** None



### Field: AppSpec.terms_of_service

**Type:** str | None

**Default Value:** None



### Field: AppSpec.model_directory

**Type:** str

**Default Value:** models

**Description:** directory to load models from



### Field: AppSpec.libs_directory

**Type:** str

**Default Value:** libs

**Description:** directory to add into PYTHONPATH



### Field: AppSpec.databases

**Type:** list[aurelix.schema.DatabaseSpec] | None

**Default Value:** None

**Description:** list of databases



### Field: AppSpec.oidc_discovery_endpoint

**Type:** str | None

**Default Value:** None

**Description:** OIDC discovery endpoint for authentication



### Field: AppSpec.views

**Type:** AppViewsSpec

**Default Value:** PydanticUndefined

**Description:** List of views to register on this app


# Configuration Options

## AppViewsSpec



### Field: AppViewsSpec.well_known_config

**Type:** ViewSpec

**Default Value:** PydanticUndefined



### Field: AppViewsSpec.extensions

**Type:** dict[str, aurelix.schema.ExtensionViewSpec] | None

**Default Value:** None


# Configuration Options

## ModelSpec



### Field: ModelSpec.name

**Type:** str

**Default Value:** PydanticUndefined

**Description:** Name of model



### Field: ModelSpec.storageType

**Type:** StorageTypeSpec

**Default Value:** PydanticUndefined

**Description:** Type of storage to store this model in



### Field: ModelSpec.fields

**Type:** dict[str, aurelix.schema.FieldSpec]

**Default Value:** PydanticUndefined

**Description:** List of fields/properties this model have



### Field: ModelSpec.defaultFieldPermission

**Type:** FieldPermission

**Default Value:** readWrite

**Description:** Default permission for fields



### Field: ModelSpec.views

**Type:** ModelViewsSpec

**Default Value:** PydanticUndefined

**Description:** List of views this model have



### Field: ModelSpec.tags

**Type:** list[str] | None

**Default Value:** PydanticUndefined

**Description:** OpenAPI tag which this model shall be tagged under



### Field: ModelSpec.stateMachine

**Type:** aurelix.schema.StateMachineSpec | None

**Default Value:** None

**Description:** StateMachine specification for this model for workflow support



### Field: ModelSpec.beforeCreate

**Type:** list[aurelix.schema.CodeRefSpec] | None

**Default Value:** None

**Description:** Event hook, before item is insert into database



### Field: ModelSpec.afterCreate

**Type:** list[aurelix.schema.CodeRefSpec] | None

**Default Value:** None

**Description:** Event hook, after item have been inserted into database



### Field: ModelSpec.beforeUpdate

**Type:** list[aurelix.schema.CodeRefSpec] | None

**Default Value:** None

**Description:** Event hook, before item is updated in database



### Field: ModelSpec.afterUpdate

**Type:** list[aurelix.schema.CodeRefSpec] | None

**Default Value:** None

**Description:** Event hook, after item is updated in database



### Field: ModelSpec.beforeDelete

**Type:** list[aurelix.schema.CodeRefSpec] | None

**Default Value:** None

**Description:** Event hook, before item deleted in database



### Field: ModelSpec.afterDelete

**Type:** list[aurelix.schema.CodeRefSpec] | None

**Default Value:** None

**Description:** Event hook, after item is deleted in database



### Field: ModelSpec.transformCreateData

**Type:** list[aurelix.schema.CodeRefSpec] | None

**Default Value:** None

**Description:** Transform hook, to transform item before inserted into database



### Field: ModelSpec.transformUpdateData

**Type:** list[aurelix.schema.CodeRefSpec] | None

**Default Value:** None

**Description:** Transform hook, to transform item before updated in database



### Field: ModelSpec.transformOutputData

**Type:** list[aurelix.schema.CodeRefSpec] | None

**Default Value:** None

**Description:** Transform hook, before item is returned for display



### Field: ModelSpec.permissionFilters

**Type:** list[aurelix.schema.PermissionFilterSpec] | None

**Default Value:** None

**Description:** Permission rules for rows and field security



### Field: ModelSpec.validators

**Type:** list[aurelix.schema.CodeRefSpec] | None

**Default Value:** None

**Description:** Event hook, for validating model before insert/update into database



### Field: ModelSpec.maxPageSize

**Type:** int

**Default Value:** 100

**Description:** Maximum number of items in listing pages


# Configuration Options

## ModelViewsSpec



### Field: ModelViewsSpec.listing

**Type:** ViewSpec

**Default Value:** PydanticUndefined



### Field: ModelViewsSpec.create

**Type:** ViewSpec

**Default Value:** PydanticUndefined



### Field: ModelViewsSpec.read

**Type:** ViewSpec

**Default Value:** PydanticUndefined



### Field: ModelViewsSpec.update

**Type:** ViewSpec

**Default Value:** PydanticUndefined



### Field: ModelViewsSpec.delete

**Type:** ViewSpec

**Default Value:** PydanticUndefined



### Field: ModelViewsSpec.extensions

**Type:** dict[str, aurelix.schema.ExtensionViewSpec] | None

**Default Value:** None


# Configuration Options

## ViewSpec



### Field: ViewSpec.enabled

**Type:** bool

**Default Value:** True


