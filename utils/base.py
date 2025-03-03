import jwt
import uuid
from typing import List
from functools import wraps
from datetime import datetime
from users.models import User
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from dateutil.parser import parse
from ninja.errors import HttpError
from ninja.security import HttpBearer

TOKEN_EXPIRY = {
    "login": timedelta(days=3),
    "new_user": timedelta(days=2),
    "password_reset": timedelta(hours=1),
}


def get_authenticated_user(request) -> User:
    if not isinstance(request.auth, User):
        raise HttpError(401, "Unauthorized: Invalid authentication")
    
    try:
        return User.objects.get(username=request.auth)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")


def check_if_is_staff(request):
    user = get_authenticated_user(request)
    
    if not user.is_staff:
        raise HttpError(401, "Unauthorized")


def check_if_is_active(request):
    user = get_authenticated_user(request)
    
    if not user.is_active:
        raise HttpError(401, "Inactive account. Contact administrator.")


def check_user_role(request, is_artist: bool):
    user = get_authenticated_user(request)

    if user.is_artist == True and is_artist == False:
        raise HttpError(401, f"User is not a buyer.")
    elif user.is_artist == False and is_artist == True:
        raise HttpError(401, f"User is not an artist.")


def require_role(is_artist: bool):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):

            check_user_role(request, is_artist)

            return func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_active(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        check_if_is_active(request)

        return func(request, *args, **kwargs)

    return wrapper


def get_expiry_duration(token_type: str) -> timedelta:
    return TOKEN_EXPIRY.get(token_type, timedelta(days=1))


def login_jwt(user: User) -> str | None:
    try:
        expiry_date = timezone.now() + get_expiry_duration("login")

        token = jwt.encode(
            {
                "id": str(user.id),
                "username": user.username,
                "is_artist": user.is_artist,
                "expires": expiry_date.timestamp(),
                "iat": timezone.now().timestamp(),
            },
            settings.SECRET_KEY,
            algorithm="HS256",
        )

        return token
    except Exception as e:
        raise Exception(str(e))


def password_reset_jwt(user: User) -> str | None:
    try:
        expiry_date = timezone.now() + get_expiry_duration("password_reset")

        token = jwt.encode(
            {
                "id": str(user.id),
                "username": user.username,
                "is_artist": user.is_artist,
                "expires": expiry_date.timestamp(),
                "iat": timezone.now().timestamp(),
            },
            settings.SECRET_KEY,
            algorithm="HS256",
        )

        return token
    except Exception as e:
        raise Exception(str(e))


def decode_jwt(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        if "expires" in payload and timezone.now().timestamp() > payload["expires"]:
            raise Exception("Token has expired")

        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("The token has expired. Please login again.")
    except jwt.DecodeError:
        raise Exception("The token is invalid or malformed.")
    except Exception as e:
        raise Exception(str(e))


class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        if token:
            try:
                payload = decode_jwt(token)

                if payload and "username" in payload:
                    return User.objects.get(username=payload["username"])
            except User.DoesNotExist:
                raise Exception("User associated with this token does not exist.")
            except Exception as e:
                raise Exception(f"Authentication failed: {str(e)}")


def get_client_ip(request):
    LOCAL_IP_PREFIXES = (
        "127.",  # Localhost IP (IPv4)
        "10.",  # Private network range 10.0.0.0 - 10.255.255.255
        "192.168.",  # Private network range 192.168.0.0 - 192.168.255.255
        "172.",  # Private network range 172.16.0.0 - 172.31.255.255
    )

    try:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[-1].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")

        if ip == "localhost" or any(
            ip.startswith(prefix) for prefix in LOCAL_IP_PREFIXES
        ):
            raise Exception("Local IP address detected. Cannot determine external IP.")

        return ip
    except Exception as e:
        raise Exception(str(e))


def parse_html_date(date: str):
    try:
        datetime_value = parse(date)
        date_value = datetime_value.date()

        return {
            "datetime": datetime_value,
            "date": date_value,
        }
    except ValueError as e:
        raise ValueError(f"Invalid date format: {e}")


def parse_uuid(id: str) -> uuid.UUID:
    try:
        return uuid.UUID(id)
    except ValueError:
        raise HttpError(400, f"Invalid UUID: {id}")
