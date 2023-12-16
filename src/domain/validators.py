from domain.settings import settings


def validate_setting():
    checks = {
        "host": settings.EMAIL_HOST,
        "port": settings.EMAIL_PORT,
        "username": settings.EMAIL_USERNAME,
        "password": settings.EMAIL_PASSWORD,
    }

    errors = []

    for key, value in checks.items():
        if not value:
            errors.append(f"Please set the {key.upper()}")

    return errors
