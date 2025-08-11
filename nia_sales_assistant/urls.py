"""
URL configuration for nia_sales_assistant project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path


def redirect_to_admin(request):
    """Redirect root URL to admin panel"""
    return redirect("/admin/")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/ai/", include("ai_service.urls")),
    path("api/voice/", include("voice_service.urls")),
    path("meeting/", include("meeting_service.urls")),
    path("admin-config/", include("admin_config.urls")),
    path("", redirect_to_admin, name="home"),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0]
    )
