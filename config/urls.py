from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from portfolio.views import HomeView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", HomeView.as_view(), name="home"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
