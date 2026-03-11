"""
ASGI config for conf project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

from django.core.asgi import get_asgi_application


def bootstrap_env():
    if load_dotenv is None:
        return

    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        # Prioriza o .env local para evitar token/configuracao legada no ambiente do SO.
        load_dotenv(dotenv_path=env_file, override=True, encoding="utf-8-sig")


bootstrap_env()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')

application = get_asgi_application()
