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
from django.urls import include
from django.contrib.auth import views as auth_views
from clientes.views import redirigir_usuario
from clientes import views as cliente_views
from clientes.views import panel_cliente

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', clientes_views.redirigir_usuario, name='home'),  # SOLO la raíz
    path('clientes/', include('clientes.urls')),  # apartado accesible
    path('admin/', admin.site.urls),
    path('rutinas/', include('rutinas.urls')),
    path('dietas/', include('dietas.urls')),
    path('entrenos/', include('entrenos.urls')),  # <-- añade esta línea
    path('panel/', clientes_views.dashboard, name='dashboard'),
    path('joi/', include('joi.urls')),
    path('register/', cliente_views.register_view, name='register'),
    path('mi-panel/', panel_cliente, name='panel_cliente'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    path('redirigir/', redirigir_usuario, name='redirigir_usuario'),
    path('logros/', include('logros.urls')),
    # API para Liftin
    path('api/liftin/', include('entrenos.urls_api')),

    # Página principal (opcional)
    path('', include('entrenos.urls')),  # Redirigir a dashboard de entrenos
    # Admin
    path('admin/', admin.site.urls),
    path('analytics/', include('analytics.urls')),
]
# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
