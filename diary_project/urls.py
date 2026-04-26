from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.conf.urls.i18n import i18n_patterns
from django.urls import path, include

urlpatterns = [
    path('', include('frontend.urls')),

    path('admin/', admin.site.urls),

    path('api/v1/', include('api.v1.urls')),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('i18n/', include('django.conf.urls.i18n')),
]