from ninja import Router
from django.conf import settings
from django.db import transaction
from ninja.errors import HttpError
from django.contrib.auth import authenticate
from users.models import User, ArtistProfile
from utils.base import (
    login_jwt,
    AuthBearer,
    decode_jwt,
    require_role,
    require_active,
    get_authenticated_user,
)
from .schema import (
    UserSchema,
    LoginUserSchema,
    UserInputSchema1,
    UserInputSchema2,
    ArtistProfileSchema,
    ArtistProfileInputSchema1,
    ArtistProfileInputSchema2,
)

router = Router()

bearer = AuthBearer()


@router.post("account", response=dict)
def create_account(request, data: UserInputSchema1):
    with transaction.atomic():
        if (
            not User.objects.filter(username=data.username).exists()
            or not User.objects.filter(email=data.email).exists()
        ):
            new_user = User.objects.create(
                username=data.username,
                email=data.email,
                is_artist=data.is_artist,
            )
        else:
            raise HttpError(400, "Username or email already exists!")

        if len(data.password) <= 8:
            raise HttpError(
                400, "Password is too short. Must have minimum of 8 characters!"
            )

        if data.password != data.confirm_password:
            raise HttpError(400, "Passwords provided did not match!")

        new_user.set_password(data.password)

        new_user.save()

    return {"message": "Account created successfully"}


@router.get(
    "account",
    auth=bearer,
    response=ArtistProfileSchema | UserSchema,
)
@require_active
def view_my_profile(request):
    user = get_authenticated_user(request)

    if ArtistProfile.objects.filter(user=user).exists():
        return ArtistProfile.objects.get(user=user)
    else:
        return user


@router.put("account", auth=bearer, response=dict)
@require_active
def update_profile(request, data: UserInputSchema2):
    user = get_authenticated_user(request)

    if data.username:
        user.username = data.username

    if data.email:
        user.email = data.email

    if data.first_name:
        user.first_name = data.first_name

    if data.last_name:
        user.last_name = data.last_name

    if data.bio:
        user.bio = data.bio

    if data.country:
        user.country = data.country

    if data.website:
        user.website = data.website

    user.save()

    return {"message": "User profile updated successfully"}


@router.post("profile", response=dict)
@require_active
@require_role(is_artist=True)
def create_artist_profile(request, data: ArtistProfileInputSchema1):
    user = get_authenticated_user(request)

    ArtistProfile.objects.create(
        user=user,
        store_name=data.store_name,
    )

    return {"message": "Artist profile created successfully"}


@router.put("profile", response=dict)
@require_active
@require_role(is_artist=True)
def update_artist_profile(request, data: ArtistProfileInputSchema2):
    user = get_authenticated_user(request)

    artist_profile = ArtistProfile.objects.get(user=user)
    
    if data.store_name:
        artist_profile.store_name = data.store_name
        
    if data.about:
        artist_profile.about = data.about
        
    artist_profile.save()

    return {"message": "Artist profile updated successfully"}
