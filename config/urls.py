from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth import login as auth_login
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpRequest
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import RedirectView
from django.views.decorators.csrf import csrf_exempt

from portfolio.views import BlogCreateView, BlogDetailView, BlogListView, HomeView, KnowledgeGraphAPIView


@csrf_exempt
def admin_login_passthrough(request, *args, **kwargs):
    form = AdminAuthenticationForm(request, data=request.POST or None)

    next_url = request.GET.get("next") or request.POST.get("next") or "/admin/"
    if not url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={*settings.ALLOWED_HOSTS, request.get_host().split(":")[0]},
        require_https=request.is_secure(),
    ):
        next_url = "/admin/"

    if request.method == "POST" and form.is_valid():
        auth_login(request, form.get_user())
        return redirect(next_url)

    context = {
        **admin.site.each_context(request),
        "title": "Log in",
        "app_path": request.get_full_path(),
        "next": next_url,
        "form": form,
    }
    return TemplateResponse(request, "admin/login.html", context)

urlpatterns = [
    path("admin/login/", admin_login_passthrough, name="admin-login"),
    path("admin/", admin.site.urls),
    path("accounts/login/", RedirectView.as_view(url="/admin/login/", permanent=False)),
    path("home", RedirectView.as_view(url="/", permanent=False)),
    path("home/", RedirectView.as_view(url="/", permanent=False)),
    path("", HomeView.as_view(), name="home"),
    path("blog/", BlogListView.as_view(), name="blog-list"),
    path("blog/write/", BlogCreateView.as_view(), name="blog-write"),
    path("blog/<slug:slug>/", BlogDetailView.as_view(), name="blog-detail"),
    path("api/knowledge-graph/", KnowledgeGraphAPIView.as_view(), name="knowledge-graph-api"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
