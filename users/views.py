from .models import User
from datetime import datetime
from urllib.parse import quote
from django.conf import settings
from utils.base import decode_jwt
from django.shortcuts import render
from django.contrib import messages


def update_password(request):
    reset_token = request.GET.get("reset_token")

    if reset_token:
        request.session["reset_token"] = reset_token

    context = {"redirect_url": ""}

    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if len(password) <= 8:
            messages.error(
                request, "Password is too short. Must have minimum of 8 characters!"
            )

            return render(request, "auth/password_update.html", context)

        if password != confirm_password:
            messages.error(request, "Passwords provided did not match!")

            return render(request, "auth/password_update.html", context)

        try:
            verified_credentials = decode_jwt(request.session["reset_token"])

            expiry_date = verified_credentials["expires"]  # type: ignore

            current_time = datetime.now().timestamp()

            if current_time - expiry_date <= 0:
                user = User.objects.get(username=verified_credentials["username"])  # type: ignore

                user.set_password(password)
                user.save()

                redirect_url = f"{settings.FRONTEND_URL}/auth/sign-in"

                context["redirect_url"] = redirect_url
            else:
                messages.error(request, "Your password reset token has expired.")

                return render(request, "auth/password_update.html", context)

            del request.session["reset_token"]
        except Exception as e:
            messages.error(request, f"Session expired or missing: {str(e)}.")

            return render(request, "auth/password_update.html", context)

    return render(request, "auth/password_update.html", context)
