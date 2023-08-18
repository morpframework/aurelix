class AurelixException(Exception):
    def __init__(self, message, *args):
        self.message = message
        super().__init__(*args)

class SearchException(AurelixException):
    pass

