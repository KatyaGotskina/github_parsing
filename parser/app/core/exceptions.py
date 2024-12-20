class DomainError(Exception):
    pass


class DBError(DomainError):
    pass


class NotFoundError(DomainError):
    pass
