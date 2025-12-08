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
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
# Importa tus vistas personalizadas
from  personal.views import custom_page_not_found, custom_permission_denied
from django.contrib.auth.views import LogoutView
from personal.views import CustomLoginView
from django.contrib.auth import views as auth_views

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

    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('tutorial/', TemplateView.as_view(template_name='tutorial_sistema.html'), name='tutorial_sistema'),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
