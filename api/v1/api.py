from ninja import NinjaAPI
from http import HTTPStatus
from django.http import Http404
from django.core.exceptions import (
    FieldError,
    ValidationError,
    PermissionDenied,
    ObjectDoesNotExist,
    SuspiciousOperation,
    MultipleObjectsReturned,
)
from django.core.exceptions import (
    ObjectDoesNotExist,
    ValidationError,
    PermissionDenied,
)
from django.db import DatabaseError, IntegrityError, DataError
from ninja.errors import ValidationError as NinjaValidationError

api = NinjaAPI(urls_namespace="rems_api_v1", version="1.0.0")

"""
NOTE: Registration of endpoints here 👇
"""

from users.api.v1.api import router as users_router

api.add_router(
    "auth/",
    users_router,
    tags=["User Authentication"],
)

"""
NOTE: Registration of endpoints here 👆
"""


@api.exception_handler(ObjectDoesNotExist)
def handle_object_does_not_exist(request, exc):
    return api.create_response(
        request,
        {"message": "ObjectDoesNotExist", "detail": str(exc)},
        status=HTTPStatus.NOT_FOUND,
    )


@api.exception_handler(PermissionDenied)
def handle_permission_error(request, exc: PermissionDenied):
    return api.create_response(
        request,
        {
            "message": "PermissionDenied",
            "detail": "You don't have the permission to access this resource.",
        },
        status=HTTPStatus.FORBIDDEN,
    )


@api.exception_handler(NinjaValidationError)
def handle_ninja_validation_error(request, exc: NinjaValidationError):
    mapped_msg = {error["loc"][-1]: error["msg"] for error in exc.errors}
    return api.create_response(
        request,
        data={"message": "NinjaValidationError", "detail": mapped_msg},
        status=HTTPStatus.BAD_REQUEST,
    )


@api.exception_handler(ValidationError)
def handle_validation_error(request, exc: ValidationError):
    status = HTTPStatus.BAD_REQUEST
    for field, errors in exc.error_dict.items():  # type: ignore
        for error in errors:
            if error.code in ["unique", "unique_together"]:
                status = HTTPStatus.CONFLICT
    return api.create_response(
        request,
        data={"message": "ValidationError", "detail": exc.message_dict},
        status=status,
    )


@api.exception_handler(FieldError)
def handle_field_error(request, exc: FieldError):
    return api.create_response(
        request,
        data={"message": "FieldError", "detail": str(exc)},
        status=HTTPStatus.BAD_REQUEST,
    )


@api.exception_handler(MultipleObjectsReturned)
def handle_multiple_objects_returned(request, exc: MultipleObjectsReturned):
    return api.create_response(
        request,
        {"message": "MultipleObjectsReturned", "detail": str(exc)},
        status=HTTPStatus.CONFLICT,
    )


@api.exception_handler(Http404)
def handle_http_404(request, exc: Http404):
    return api.create_response(
        request,
        {"message": "Not Found", "detail": str(exc)},
        status=HTTPStatus.NOT_FOUND,
    )


@api.exception_handler(ValueError)
def handle_value_error(request, exc: ValueError):
    return api.create_response(
        request,
        {"message": "ValueError", "detail": str(exc)},
        status=HTTPStatus.BAD_REQUEST,
    )


@api.exception_handler(IntegrityError)
def handle_integrity_error(request, exc: IntegrityError):
    return api.create_response(
        request,
        {"message": "IntegrityError", "detail": str(exc)},
        status=HTTPStatus.CONFLICT,
    )


@api.exception_handler(DatabaseError)
def handle_database_error(request, exc: DatabaseError):
    return api.create_response(
        request,
        {"message": "DatabaseError", "detail": str(exc)},
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
    )


@api.exception_handler(DataError)
def handle_data_error(request, exc: DataError):
    return api.create_response(
        request,
        {"message": "DataError", "detail": str(exc)},
        status=HTTPStatus.BAD_REQUEST,
    )


@api.exception_handler(SuspiciousOperation)
def handle_suspicious_operation(request, exc: SuspiciousOperation):
    return api.create_response(
        request,
        {"message": "SuspiciousOperation", "detail": str(exc)},
        status=HTTPStatus.BAD_REQUEST,
    )


# Fallback catch-all handler – use with caution!
@api.exception_handler(Exception)
def handle_general_exception(request, exc: Exception):
    return api.create_response(
        request,
        {"message": "Internal Server Error", "detail": str(exc)},
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
    )
