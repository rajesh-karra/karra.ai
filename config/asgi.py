import os

from django.core.asgi import get_asgi_application
from starlette.applications import Starlette
from starlette.routing import Mount

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

from api.app import fastapi_app  # noqa: E402

application = Starlette(
    routes=[
        Mount("/api", app=fastapi_app),
        Mount("/", app=django_asgi_app),
    ]
)
