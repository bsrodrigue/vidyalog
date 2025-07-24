class VidyalogError(Exception):
    def __init__(self, message, message_markup=None, *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        self.message = message
        self.message_markup = message_markup
