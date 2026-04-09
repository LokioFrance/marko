import os

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.permissions import AllowAny

from .honeypot import honeypot_admin

schema_view = get_schema_view(
    openapi.Info(
        title="Marko API",
        default_version="v1",
        description="API de gestion des identifiants (QR codes, barcodes).",
    ),
    public=True,
    permission_classes=[AllowAny],
)

_admin_url = os.environ.get("DJANGO_ADMIN_URL", "").strip("/")
if not _admin_url:
    raise RuntimeError(
        "La variable d'environnement DJANGO_ADMIN_URL n'est pas définie. "
        "Ajoutez-la dans votre fichier .env (ex: DJANGO_ADMIN_URL=mon-panneau-secret/)."
    )

urlpatterns = [
    # ── Vraie interface admin (URL secrète) ───────────────────────────────────
    path(f"{_admin_url}/", admin.site.urls),

    # ── Honeypot sur /admin/ ──────────────────────────────────────────────────
    re_path(r"^admin/", honeypot_admin),

    # ── API ───────────────────────────────────────────────────────────────────
    path("api-auth/", include("rest_framework.urls")),
    path("api/", include("api.urls")),

    # ── Swagger / ReDoc ───────────────────────────────────────────────────────
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]

# Servir les médias en développement (QR codes, barcodes)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
