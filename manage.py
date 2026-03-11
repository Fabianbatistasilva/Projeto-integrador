#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback for incomplete local env
    load_dotenv = None


def bootstrap_env():
    if load_dotenv is None:
        return

    env_file = Path(__file__).resolve().parent / ".env"
    if env_file.exists():
        # Prioriza o .env local para evitar token/configuracao legada no ambiente do SO.
        load_dotenv(dotenv_path=env_file, override=True, encoding="utf-8-sig")


def main():
    """Run administrative tasks."""
    bootstrap_env()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
