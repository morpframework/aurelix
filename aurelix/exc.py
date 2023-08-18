class AetherException(Exception):
    def __init__(self, message, *args):
        self.message = message
        super().__init__(*args)

class SearchException(AetherException):
    pass

