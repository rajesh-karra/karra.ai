from django.conf import settings


def app_meta(_request):
    return {"APP_VERSION": settings.APP_VERSION}
