from . import views
from django.urls import path

urlpatterns = [
    path(
        "update_password",
        views.update_password,
        name="update_password",
    ),
]
