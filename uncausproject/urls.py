"""
URL configuration for uncausproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
# Importa tus vistas personalizadas
from  personal.views import custom_page_not_found, custom_permission_denied
from django.contrib.auth.views import LogoutView
from personal.views import CustomLoginView

# Asigna los handlers
handler404 = custom_page_not_found
handler403 = custom_permission_denied


urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('admin/', admin.site.urls),
    path('personal/', include('personal.urls')),
    path('',include('habitaciones.urls')),
    path('internacion/',include('internacion.urls')),
    path('pacientes/',include('pacientes.urls')),
    path('select2/', include('django_select2.urls')),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
