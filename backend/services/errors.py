"""Service failures mapped to HTTP only at the boundary."""


class AuthenticationError(ValueError):
    pass


class AssignmentNotFound(ValueError):
    pass
