class ServiceError(Exception):
    status_code = 400
    detail = "Service error."

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class NotFoundServiceError(ServiceError):
    status_code = 404
    detail = "Resource not found."


class ConflictServiceError(ServiceError):
    status_code = 409
    detail = "Conflict."


class ValidationServiceError(ServiceError):
    status_code = 422
    detail = "Validation error."
