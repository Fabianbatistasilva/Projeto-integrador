from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render


def _client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return str(forwarded_for).split(",")[0].strip()
    return str(request.META.get("REMOTE_ADDR") or "unknown").strip()


def _login_throttle_key(request, username):
    normalized_user = str(username or "").strip().lower()
    return f"login_attempt::{_client_ip(request)}::{normalized_user}"


def UserLogin(request):
    if request.method == "POST":
        nome = request.POST.get("username")
        senha = request.POST.get("password")
        throttle_key = _login_throttle_key(request, nome)
        max_attempts = int(getattr(settings, "LOGIN_MAX_ATTEMPTS", 5))
        block_seconds = int(getattr(settings, "LOGIN_BLOCK_SECONDS", 300))
        failed_attempts = int(cache.get(throttle_key, 0) or 0)

        if failed_attempts >= max_attempts:
            messages.info(request, "Muitas tentativas de login. Aguarde alguns minutos e tente novamente.")
            return render(request, "paginas/login.html")

        check = auth.authenticate(request, username=nome, password=senha)
        if check is not None:
            cache.delete(throttle_key)
            login(request, check)
            return redirect("home")

        cache.set(throttle_key, failed_attempts + 1, timeout=block_seconds)
        messages.info(request, "Login invalido.")
        return render(request, "paginas/login.html")

    return render(request, "paginas/login.html")


def UserLogout(request):
    logout(request)
    return redirect("login_site")


def UserRegistration(request):
    if request.method != "POST":
        return render(request, "paginas/registration_screen.html")

    nome = str(request.POST.get("username") or "").strip()
    senha = str(request.POST.get("password") or "")
    conf_senha = str(request.POST.get("conf_password") or "")

    if nome == "" or senha == "" or conf_senha == "":
        messages.info(request, "Preencha todos os campos.")
        return render(request, "paginas/registration_screen.html")

    if User.objects.filter(username=nome).exists():
        messages.info(request, "Usuario ja existe.")
        return render(request, "paginas/registration_screen.html")

    if senha != conf_senha:
        messages.info(request, "As senhas nao conferem.")
        return render(request, "paginas/registration_screen.html")

    try:
        validate_password(senha, user=User(username=nome))
    except ValidationError as error:
        for message in error.messages:
            messages.info(request, message)
        return render(request, "paginas/registration_screen.html")

    User.objects.create_user(username=nome, password=senha)
    return redirect("login_site")

