from ninja import ModelSchema, Schema
from typing import Optional, Literal, Union
from users.models import User, ArtistProfile
from pydantic import Field, model_validator, EmailStr


class UserSchema(ModelSchema):
    class Meta:
        model = User
        exclude = [
            "groups",
            "country",
            "password",
            "is_staff",
            "is_active",
            "last_login",
            "is_superuser",
            "user_permissions",
        ]


class ArtistProfileSchema(ModelSchema):
    class Meta:
        model = ArtistProfile
        fields = "__all__"
        depth = 1
        exclude = ["user"]

    user: UserSchema


PASSWORD_DESC = "Password must have at least 8 characters"


class EmailVerificationSchema(Schema):
    email: EmailStr


class UserPasswordResetSchema(Schema):
    email: EmailStr


class UserInputSchema1(Schema):
    username: str
    is_artist: bool
    password: str = Field(..., min_length=8, description=PASSWORD_DESC)
    confirm_password: str = Field(..., min_length=8, description=PASSWORD_DESC)

    @model_validator(mode="after")
    def check_passwords_match(self) -> "UserInputSchema1":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match!")

        return self


class UserInputSchema2(Schema):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = None


class LoginUserSchema(Schema):
    username: str
    password: str = Field(..., min_length=8, description=PASSWORD_DESC)


class ArtistProfileInputSchema1(Schema):
    store_name: str
    about: str


class ArtistProfileInputSchema2(Schema):
    store_name: Optional[str] = None
    about: Optional[str] = None
    stripe_secret_key: Optional[str] = None
