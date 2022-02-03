class KnownError(Exception):
    pass


class SlackError(KnownError):
    pass


class GradescopeError(KnownError):
    pass


class SheetError(KnownError):
    pass


class StudentRecordError(KnownError):
    pass


class ConfigurationError(KnownError):
    pass


class FormInputError(KnownError):
    pass


class EmailError(KnownError):
    pass
