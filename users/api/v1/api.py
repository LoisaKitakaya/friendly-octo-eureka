from ninja import Router, File
from django.conf import settings
from django.db import transaction
from ninja.errors import HttpError
from utils.tasks import send_email
from ninja.files import UploadedFile
from django.contrib.auth import authenticate
from users.models import User, ArtistProfile
from utils.base import (
    login_jwt,
    AuthBearer,
    decode_jwt,
    new_user_jwt,
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
    EmailVerificationSchema,
    ArtistProfileInputSchema1,
    ArtistProfileInputSchema2,
)

router = Router()

bearer = AuthBearer()


@router.post(
    "email-verification",
    response=dict,
)
def email_verification(
    request,
    data: EmailVerificationSchema,
):
    if User.objects.filter(email=data.email).exists():
        raise HttpError(400, "A user with the same email address already exists.")

    verification_token = new_user_jwt(email=data.email)

    forward_url = settings.FRONTEND_URL

    verification_url = (
        f"{forward_url}/auth/create-account?verification_token={verification_token}"
    )

    subject = "Email Verification"

    message = f"To complete account verification, click the following link: {verification_url}"

    send_email.delay(
        subject=subject,
        message=message,
        receiver_email_address=data.email,
    )

    return {"message": f"A verification email has been sent to {data.email}"}


@router.post("account", response=dict)
def create_account(request, data: UserInputSchema1, verification_token):
    verification_token = decode_jwt(verification_token)

    with transaction.atomic():
        if (
            not User.objects.filter(username=data.username).exists()
            or not User.objects.filter(email=data.email).exists()
        ):
            new_user = User.objects.create(
                username=data.username,
                email=verification_token.get("email"),
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


@router.post("account/profile-pic", auth=bearer, response=dict)
@require_active
def update_profile_pic(
    request,
    file: UploadedFile = File(...),  # type: ignore
):
    user = get_authenticated_user(request)

    user.profile_picture.save(file.name, file, save=True)

    return {"message": "Profile picture updated successfully"}


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

    if data.website:
        user.website = data.website

    user.save()

    return {"message": "User profile updated successfully"}


@router.post("profile", auth=bearer, response=dict)
@require_active
@require_role(is_artist=True)
def create_artist_profile(request, data: ArtistProfileInputSchema1):
    user = get_authenticated_user(request)

    ArtistProfile.objects.create(
        user=user,
        store_name=data.store_name,
        about=data.about,
    )

    return {"message": "Artist profile created successfully"}


@router.put("profile", auth=bearer, response=dict)
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


@router.post("profile/banner-pic", auth=bearer, response=dict)
@require_active
def update_banner_pic(
    request,
    file: UploadedFile = File(...),  # type: ignore
):
    user = get_authenticated_user(request)

    artist_profile = ArtistProfile.objects.get(user=user)

    artist_profile.banner_image.save(file.name, file, save=True)

    return {"message": "Banner picture updated successfully"}


@router.post("login", response=dict)
def login(request, data: LoginUserSchema):
    user_ = authenticate(username=data.username, password=data.password)

    if user_ is not None:
        user = User.objects.get(username=data.username)

        if not user.is_active:
            raise HttpError(401, "Inactive account. Contact administrator.")

        auth_token = login_jwt(user)

        return {
            "token": auth_token,
            "id": str(user.id),
            "username": user.username,
            "is_artist": user.is_artist,
            "message": "Authentication successful",
        }

    else:
        raise HttpError(401, "Authentication failed: Wrong email or password")
