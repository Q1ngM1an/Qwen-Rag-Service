from fastapi import HTTPException

from core.domain_exceptions import DomainError


def raise_http_error(exc: DomainError):
    raise HTTPException(status_code=exc.status_code, detail=exc.message)
