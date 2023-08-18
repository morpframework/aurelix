class AurelixException(Exception):
    status_code = 500

    def __init__(self, message, *args):
        self.message = message
        super().__init__(*args)

class SearchException(AurelixException):
    status_code = 422

class CollectionNotFoundException(AurelixException):
    status_code = 404

    def __init__(self, message, *args):
        message = 'Could not found collection in context %s' % message
        super().__init__(message, *args)   

class RecordNotFoundException(AurelixException):
    status_code = 404

    def __init__(self, message, *args):
        message = 'Could not found record with identifier = %s' % message
        super().__init__(message, *args)