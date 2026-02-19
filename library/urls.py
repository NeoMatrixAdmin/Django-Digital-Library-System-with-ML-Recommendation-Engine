from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    # API must come BEFORE redirect
    path('api/', include('catalog.api.urls')),
    # Main catalog app
    path('catalog/', include('catalog.urls')),
    # Authentication
    path('accounts/', include('allauth.urls')),
    # Redirect root URL to catalog homepage
    path('', RedirectView.as_view(url='catalog/')),
    # Dashboard app  <-- THIS IS WHAT YOU ARE MISSING
    path("dashboard/", include(("dashboard.urls", "dashboard"), namespace="dashboard")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
