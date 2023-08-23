# Changelog for Aurelix

## 0.1.2b3 (2023-08-24)

- added object storage support for object uploads
- added field editing guard for object storage fields and workflow fields

## 0.1.2b2 (2023-08-23)

- Added hooks for field and model validation
- allow specifying function name in CodeRefSpec
- added field input/output transfomer hooks
- added alembic support

## 0.1.2.beta1 (2023-08-22)

- fixed after/before create/update/delete event hooks not triggering
- fixed transform create/update/output transform hooks not overriding correctly
- event hooks and transform hooks are now multi-item and chainable
- fix MANIFEST.in that caused failure to install from pip


## 0.1.1 (2023-08-21)

- added field level permission filter
- added encrypted-string field
- exclude null from response objects
- fixed startup issue when `swagger_ui_init_oauth` not configured
- added `init` cli command to initialize project

## 0.1 (2023-08-21)

- initial release
