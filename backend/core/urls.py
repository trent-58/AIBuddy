from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

def api_root(request):
    return JsonResponse({
        "message": "AI Buddy API is running.",
        "frontend": "Open the web app at http://localhost:5173",
        "docs": "/api/schema/swagger-ui/",
    })

urlpatterns = [
    path("", api_root),
    path("admin/", admin.site.urls),

    # API
    path("api/auth/", include("user.urls")),
    path("api/matching/", include("matching.urls")),
    path("api/chats/", include("chats.urls")),

    # swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
