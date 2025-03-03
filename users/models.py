import uuid
from django.db import models
from django.utils.text import slugify
from django_countries.fields import CountryField
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model for artists and buyers"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    profile_picture = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True,
    )
    is_artist = models.BooleanField(default=False)
    bio = models.TextField(blank=True, null=True)
    country = CountryField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)


class ArtistProfile(models.Model):
    """Artist-specific profile for managing their store"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="artist_profile",
    )
    banner_image = models.ImageField(
        upload_to="banners/",
        blank=True,
        null=True,
    )
    store_name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    about = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.store_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.store_name
