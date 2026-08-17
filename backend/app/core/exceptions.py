class CampusOSException(Exception):
    def __init__(self, message: str, code: str = "ERROR", status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code

class EntityNotFoundError(CampusOSException):
    def __init__(self, entity: str, entity_id: str):
        super().__init__(
            message=f"{entity} with ID {entity_id} not found.",
            code="NOT_FOUND",
            status_code=404
        )

class DuplicateSubmissionError(CampusOSException):
    def __init__(self, message: str = "An active verification request already exists for this user or email."):
        super().__init__(
            message=message,
            code="DUPLICATE_SUBMISSION",
            status_code=409
        )

class FileValidationError(CampusOSException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="INVALID_FILE",
            status_code=400
        )

class EmailValidationError(CampusOSException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="INVALID_EMAIL",
            status_code=400
        )

class ForbiddenError(CampusOSException):
    def __init__(self, message: str = "Insufficient permissions to perform this action."):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403
        )
