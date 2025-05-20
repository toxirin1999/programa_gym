"""
URL configuration for gymproject project.

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
from django.contrib import admin
from django.urls import path, include
from clientes import views as clientes_views  # o core.views si tienes app core
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', clientes_views.home),  # Página de inicio
    path('admin/', admin.site.urls),
    path('clientes/', include('clientes.urls')),
    path('rutinas/', include('rutinas.urls')),
    path('dietas/', include('dietas.urls')),
    path('entrenos/', include('entrenos.urls')),  # <-- añade esta línea
    path('anuncios/', include('anuncios.urls')),
    path('panel/', clientes_views.dashboard, name='dashboard'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
