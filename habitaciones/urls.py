from django.urls import path
from . import views
from . import estadisticas_views

urlpatterns = [
    path('', views.lista_habitaciones, name='lista_habitaciones'),
    path('habitaciones/', views.lista_habitaciones, name='lista_habitaciones'),
    path('liberar_cama/<int:idcama>/', views.liberar_cama, name='liberar_cama'),
    path('liberar_cama_reservada/<int:idcama>/', views.liberar_cama_reservada, name='liberar_cama_reservada'),
    path('reservar_cama/<int:idcama>/', views.reservar_cama, name='reservar_cama'),
    path('ver_reserva/<int:idcama>/', views.ver_reserva, name='ver_reserva'),
    path('grafico_porcentaje_internados/', views.reporte_grafico_porcentaje_internados, name='reporte_grafico_porcentaje_internados'),
    
    # URLs de estadísticas - MOVIDAS AL ARCHIVO SEPARADO
    path('estadisticas/', estadisticas_views.estadisticas_camas, name='estadisticas'),
    path('estadisticas-avanzadas/', estadisticas_views.estadisticas_avanzadas, name='estadisticas_avanzadas'),
    path('limpiar-reservas/', estadisticas_views.limpiar_reservas_vencidas, name='limpiar_reservas'),
    
    # URLs para crear entidades
    path('crear-sector/', views.crear_sector, name='crear_sector'),
    path('crear-habitacion/', views.crear_habitacion, name='crear_habitacion'),
    path('crear-cama/', views.crear_cama, name='crear_cama'),
]