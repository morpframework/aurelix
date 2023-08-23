class AurelixException(Exception):
    status_code = 500

    def __init__(self, message, *args):
        self.message = message
        super().__init__(*args)

    def __str__(self) -> str:
        return '%s.%s: %s' % (self.__class__.__module__, AurelixException.__class__.__name__, self.message)

class SearchException(AurelixException):
    status_code = 422

class ValidationError(AurelixException):
    status_code = 422

class GatewayError(AurelixException):
    status_code = 502

class Unauthorized(AurelixException):
    status_code = 401

class Forbidden(AurelixException):
    status_code = 403

class NotFound(AurelixException):
    status_code = 404

class CollectionNotFoundException(AurelixException):
    status_code = 404

    def __init__(self, message, *args):
        message = 'Could not found collection in context %s' % message
        super().__init__(message, *args)   

class RecordNotFoundException(NotFound):
    status_code = 404

    def __init__(self, message, *args):
        message = 'Could not found record with identifier = %s' % message
        super().__init__(message, *args)