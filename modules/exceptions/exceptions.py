from libs.log.file_logger import FileLogger


class VidyalogError(Exception):
    def __init__(self, message, message_markup=None, *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        self.message = message
        self.message_markup = message_markup

        logger = FileLogger(self.__class__.__name__)
        logger.error(message)


class ServiceError(VidyalogError):
    def __init__(self, message, message_markup=None, *args, **kwargs):
        super().__init__(message, message_markup=message_markup, *args, **kwargs)
