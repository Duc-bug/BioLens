from __future__ import annotations


class BioLensBaseError(Exception):
    def __init__(self, message: str, status_code: int = 400, error_code: str = "BIOLENS_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code

    def to_dict(self) -> dict:
        return {"error": self.error_code, "message": self.message}


class UnsupportedAlgorithmError(BioLensBaseError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=400, error_code="UNSUPPORTED_ALGORITHM")
