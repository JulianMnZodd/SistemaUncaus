from django.urls import path
from . import views

urlpatterns = [
    path('asignar_cama/<int:idcama>/', views.asignar_cama, name='asignar_cama'),
    path('internaciones/', views.listar_internaciones, name='listar_internaciones'),
    path('crear_diagnostico/<int:internacion_id>/', views.crear_diagnostico, name='crear_diagnostico'),
    path('detalle_diagnostico/<int:internacion_id>/', views.detalle_diagnostico, name='detalle_diagnostico'),
    path('seleccionar_cama/<int:paciente_id>/', views.seleccionar_cama, name='seleccionar_cama'),
    path('seguimiento/<int:internacion_id>/', views.seguimiento, name='seguimiento'),
    path('listar_seguimientos/<int:internacion_id>/', views.listar_seguimientos, name='listar_seguimientos'),
    path('seguimiento_detalles/<int:seguimiento_id>/', views.seguimiento_detalles, name='seguimiento_detalles'),
    path('generar_consentimiento_pdf/<int:paciente_id>/', views.generar_consentimiento_pdf, name='generar_consentimiento_pdf'),
    path('generar_consentimiento/', views.generar_consentimiento, name='generar_consentimiento'),
    path('informe-internaciones/', views.generar_informe_internaciones, name='generar_informe_internaciones'),
    path('informe-internacion/<int:internacion_id>/', views.generar_informe_internacion, name='generar_informe_internacion'),
    path('editar_diagnostico/<int:diagnostico_id>/', views.editar_diagnostico, name='editar_diagnostico'),
    path('derivar_paciente/', views.derivar_paciente, name='derivar_paciente'),
    path('informe_alta/<int:internacion_id>/', views.generar_informe_alta, name='generar_informe_alta'),
]