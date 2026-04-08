from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Estudiante
    path('estudiante-dashboard/', views.estudiante_dashboard, name='estudiante_dashboard'),
    path('estudiante-mis-cursos/', views.estudiante_mis_cursos, name='estudiante_mis_cursos'),
    path('estudiante-mis-calificaciones/', views.estudiante_mis_calificaciones, name='estudiante_mis_calificaciones'),
    path('estudiante-mis-pagos/', views.estudiante_mis_pagos, name='estudiante_mis_pagos'),
    path('estudiante-cursos-disponibles/', views.estudiante_cursos_disponibles, name='estudiante_cursos_disponibles'),
    path('estudiante-inscribir/', views.estudiante_inscribir, name='estudiante_inscribir'),
    # CAMBIO: <int:grupo_id> a <str:grupo_id>
    path('estudiante-tareas/<str:grupo_id>/', views.estudiante_tareas, name='estudiante_tareas'),
    path('estudiante-entregar-tarea/<int:tarea_id>/', views.estudiante_entregar_tarea, name='estudiante_entregar_tarea'),
    
    # Instructor
    
    path('instructor-dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    path('instructor-mis-grupos/', views.instructor_mis_grupos, name='instructor_mis_grupos'),
    path('instructor-gestionar-evaluaciones/', views.instructor_gestionar_evaluaciones, name='instructor_gestionar_evaluaciones'),
    path('instructor-registrar-evaluacion/', views.instructor_registrar_evaluacion, name='instructor_registrar_evaluacion'),
    path('instructor-tareas/<str:grupo_id>/', views.instructor_tareas, name='instructor_tareas'),
    path('instructor-crear-tarea/<str:grupo_id>/', views.instructor_crear_tarea, name='instructor_crear_tarea'),
    path('instructor-entregas-tarea/<int:tarea_id>/', views.instructor_entregas_tarea, name='instructor_entregas_tarea'),
    path('instructor-calificar-entrega/<int:entrega_id>/', views.instructor_calificar_entrega, name='instructor_calificar_entrega'),
    
    # Admin - Dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Admin - Cursos
    path('admin-gestionar-cursos/', views.admin_gestionar_cursos, name='admin_gestionar_cursos'),
    path('admin-crear-curso/', views.admin_crear_curso, name='admin_crear_curso'),
    path('admin-editar-curso/<int:curso_id>/', views.admin_editar_curso, name='admin_editar_curso'),
    path('admin-ver-curso/<int:curso_id>/', views.admin_ver_curso, name='admin_ver_curso'),
    path('admin-eliminar-curso/<int:curso_id>/', views.admin_eliminar_curso, name='admin_eliminar_curso'),
    
    # Admin - Grupos (CAMBIO: <int:grupo_id> a <str:grupo_id>)
    path('admin-gestionar-grupos/', views.admin_gestionar_grupos, name='admin_gestionar_grupos'),
    path('admin-crear-grupo/', views.admin_crear_grupo, name='admin_crear_grupo'),
    path('admin-editar-grupo/<str:grupo_id>/', views.admin_editar_grupo, name='admin_editar_grupo'),
    path('admin-ver-grupo/<str:grupo_id>/', views.admin_ver_grupo, name='admin_ver_grupo'),
    path('admin-eliminar-grupo/<str:grupo_id>/', views.admin_eliminar_grupo, name='admin_eliminar_grupo'),

    # Admin - Instructores
    path('admin-gestionar-instructores/', views.admin_gestionar_instructores, name='admin_gestionar_instructores'),
    path('admin-crear-instructor/', views.admin_crear_instructor, name='admin_crear_instructor'),
    path('admin-editar-instructor/<int:instructor_id>/', views.admin_editar_instructor, name='admin_editar_instructor'),
    path('admin-ver-instructor/<int:instructor_id>/', views.admin_ver_instructor, name='admin_ver_instructor'),
    path('admin-eliminar-instructor/<int:instructor_id>/', views.admin_eliminar_instructor, name='admin_eliminar_instructor'),
    
    # Admin - Estudiantes
    path('admin-gestionar-estudiantes/', views.admin_gestionar_estudiantes, name='admin_gestionar_estudiantes'),
    path('admin-crear-estudiante/', views.admin_crear_estudiante, name='admin_crear_estudiante'),
    path('admin-editar-estudiante/<int:estudiante_id>/', views.admin_editar_estudiante, name='admin_editar_estudiante'),
    path('admin-ver-estudiante/<int:estudiante_id>/', views.admin_ver_estudiante, name='admin_ver_estudiante'),
    path('admin-eliminar-estudiante/<int:estudiante_id>/', views.admin_eliminar_estudiante, name='admin_eliminar_estudiante'),
    
    # Admin - Reportes y Auditorías
    path('admin-reportes/', views.admin_reportes, name='admin_reportes'),
    path('admin-auditorias/', views.admin_auditorias, name='admin_auditorias'),
    
    # Mensajes
    path('mensajes/', views.mensajes, name='mensajes'),
    path('enviar-mensaje/', views.enviar_mensaje, name='enviar_mensaje'),
    path('ver-mensaje/<int:mensaje_id>/', views.ver_mensaje, name='ver_mensaje'),
]