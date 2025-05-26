from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.contrib.auth.views import LogoutView
from .views import CustomLoginView

urlpatterns = [
    path('registro/', views.registro, name='registro'),
    path('crear-medico',views.crear_medico, name='crear_medico'),
    path('crear-recepcionista/', views.crear_recepcionista, name='crear_recepcionista'),
    path('crear-enfermero/', views.crear_enfermero, name='crear_enfermero'),
    path('listar-medicos/', views.listar_medicos, name='listar_medicos'),
    path('listar-recepcionistas/', views.listar_recepcionistas, name='listar_recepcionistas'),
    path('listar-enfermeros/', views.listar_enfermeros, name='listar_enfermeros'),
    path('editar-medico/<int:medico_id>/', views.editar_medico, name='editar_medico'),
    path('editar-recepcionista/<int:recepcionista_id>/', views.editar_recepcionista, name='editar_recepcionista'),
    path('editar-enfermero/<int:id_enfermero>/', views.editar_enfermero, name='editar_enfermero'),
    path('eliminar-medico/<int:id_medico>/', views.eliminar_medico, name='eliminar_medico'),
    path('eliminar-recepcionista/<int:id_recepcionista>/', views.eliminar_recepcionista, name='eliminar_recepcionista'),
    path('eliminar-enfermero/<int:id_enfermero>/', views.eliminar_enfermero, name='eliminar_enfermero'),
]