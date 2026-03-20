from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.views.generic import RedirectView

from portfolio.views import BlogCreateView, BlogDetailView, BlogListView, HomeView, KnowledgeGraphAPIView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", RedirectView.as_view(url="/admin/login/", permanent=False)),
    path("", HomeView.as_view(), name="home"),
    path("blog/", BlogListView.as_view(), name="blog-list"),
    path("blog/write/", BlogCreateView.as_view(), name="blog-write"),
    path("blog/<slug:slug>/", BlogDetailView.as_view(), name="blog-detail"),
    path("api/knowledge-graph/", KnowledgeGraphAPIView.as_view(), name="knowledge-graph-api"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
