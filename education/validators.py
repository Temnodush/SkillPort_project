from urllib.parse import urlparse

from rest_framework.serializers import ValidationError


class YouTubeValidator:
    """Разрешает в поле только ссылки на youtube.com."""

    allowed_hosts = ("youtube.com", "www.youtube.com", "youtu.be")

    def __init__(self, field):
        self.field = field

    def __call__(self, value):
        link = dict(value).get(self.field)
        if not link:
            return

        host = urlparse(link).netloc.lower()
        if host not in self.allowed_hosts:
            raise ValidationError(
                f"Недопустимая ссылка: разрешены только ресурсы youtube.com."
            )