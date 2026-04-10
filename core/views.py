from django.shortcuts import render, redirect,reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction, connection
from django.conf import settings
from django.db import connection
from django.db.models import Count, Sum, Q 
import datetime
from django.core.paginator import Paginator
import pyodbc
from .models import (
    RolesUsuario, Usuarios, Estudiantes, Instructores, Cursos, Grupos,
    Inscripciones, Evaluaciones, Pagos, DetallesPagos, 
    Auditoria_Inscripciones, Auditoria_Evaluaciones, Auditoria_Pagos,
    Auditoria_Estudiantes, Auditoria_Entregas, Auditoria_Instructores,
    Auditoria_Cursos, Auditoria_Grupos,
    Tareas, Entregas, Mensajes,
    # Modelos fragmentados horizontales
    Estudiantes_INE, Estudiantes_Pasaporte,
    Instructores_TI, Instructores_Redes, Instructores_Otra,
    Cursos_Programacion, Cursos_Redes, Cursos_Ciberseguridad, Cursos_Otra,
    Grupos_Disponibles, Grupos_Llenos,
    # Modelos fragmentados verticales
    Estudiantes_Normales, Estudiantes_Sensibles,
    Instructores_Normales, Instructores_Cedulas
)

# ============================================
# FUNCIÓN HELPER PARA CONTEXTO DE SESIÓN
# ============================================

def set_session_context(usuario_id):
    """Establece el usuario_id en el contexto de sesión de SQL Server"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("EXEC sp_set_session_context 'usuario_id', %s", [usuario_id])
    except Exception as e:
        print(f"Error al establecer contexto de sesión: {e}")

# ============================================
# FUNCIÓN PARA OBTENER NOMBRE COMPLETO
# ============================================

def obtener_nombre_completo(usuario):
    """Obtiene el nombre completo del usuario según su rol"""
    try:
        if usuario.rol.rol_id == 2:  # Instructor
            instructor = Instructores.objects.get(usuario=usuario)
            return f"{instructor.nombre} {instructor.apellidos}"
        elif usuario.rol.rol_id == 3:  # Estudiante
            estudiante = Estudiantes.objects.get(usuario=usuario)
            return f"{estudiante.nombre} {estudiante.apellidos}"
        else:
            return usuario.email
    except:
        return usuario.email

# ============================================
# VISTAS PÚBLICAS
# ============================================

def home(request):
    return render(request, 'index.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            
            # Obtener el rol del usuario desde la base de datos
            try:
                usuario_db = Usuarios.objects.get(email=email)
                request.session['rol_id'] = usuario_db.rol.rol_id
                request.session['usuario_id'] = usuario_db.usuario_id
                
                # Establecer contexto de sesión
                set_session_context(usuario_db.usuario_id)
                
                if usuario_db.rol.rol_id == 1:
                    return redirect('admin_dashboard')
                elif usuario_db.rol.rol_id == 2:
                    return redirect('instructor_dashboard')
                else:
                    return redirect('estudiante_dashboard')
            except Usuarios.DoesNotExist:
                return render(request, 'login.html', {'error': 'Usuario no encontrado en el sistema'})
        else:
            return render(request, 'login.html', {'error': 'Credenciales inválidas'})
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

# ============================================
# VISTAS DE ESTUDIANTE
# ============================================

@login_required
def estudiante_dashboard(request):
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        estudiante = Estudiantes.objects.get(usuario=usuario)
        nombre_completo = estudiante.nombre + ' ' + estudiante.apellidos
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
        
        # Estadísticas del estudiante
        inscripciones_activas = Inscripciones.objects.filter(estudiante=estudiante, estado='Activa').count()
        cursos_completados = Inscripciones.objects.filter(estudiante=estudiante, estado='Completada').count()
        
        # Próximas tareas - CORREGIDO
        from datetime import date
        tareas_ids = Tareas.objects.filter(
            grupo__inscripciones__estudiante=estudiante,
            fecha_limite__gte=date.today()
        ).exclude(
            entregas__inscripcion__in=Inscripciones.objects.filter(estudiante=estudiante)
        ).values_list('tarea_id', flat=True).distinct()
        tareas_pendientes = len(tareas_ids)
        
    except (Usuarios.DoesNotExist, Estudiantes.DoesNotExist):
        nombre_completo = request.user.username
        mensajes_no_leidos = 0
        inscripciones_activas = 0
        cursos_completados = 0
        tareas_pendientes = 0
    
    return render(request, 'Estudiante/dashboard.html', {
        'nombre_estudiante': nombre_completo,
        'mensajes_no_leidos': mensajes_no_leidos,
        'inscripciones_activas': inscripciones_activas,
        'cursos_completados': cursos_completados,
        'tareas_pendientes': tareas_pendientes
    })

@login_required
def estudiante_mis_cursos(request):
    usuario = Usuarios.objects.get(email=request.user.username)
    estudiante = Estudiantes.objects.get(usuario=usuario)
    inscripciones = Inscripciones.objects.filter(estudiante=estudiante).select_related('grupo__curso', 'grupo__instructor')
    
    return render(request, 'Estudiante/mis_cursos.html', {'inscripciones': inscripciones})

@login_required
def estudiante_mis_calificaciones(request):
    usuario = Usuarios.objects.get(email=request.user.username)
    estudiante = Estudiantes.objects.get(usuario=usuario)
    inscripciones = Inscripciones.objects.filter(estudiante=estudiante)
    evaluaciones = Evaluaciones.objects.filter(inscripcion__in=inscripciones).select_related('inscripcion__grupo__curso')
    
    # Calcular promedio general
    promedio_general = evaluaciones.aggregate(promedio=Sum('calificacion') / Count('calificacion'))['promedio'] if evaluaciones.exists() else 0
    
    return render(request, 'Estudiante/mis_calificaciones.html', {
        'evaluaciones': evaluaciones,
        'promedio_general': round(promedio_general, 2) if promedio_general else 0
    })

@login_required
def estudiante_mis_pagos(request):
    usuario = Usuarios.objects.get(email=request.user.username)
    estudiante = Estudiantes.objects.get(usuario=usuario)
    inscripciones = Inscripciones.objects.filter(estudiante=estudiante)
    
    pagos = Pagos.objects.filter(
        inscripcion__in=inscripciones
    ).select_related(
        'inscripcion__grupo__curso'
    ).prefetch_related('detalles')
    
    # Descifrar referencias de pago
    with connection.cursor() as cursor:
        for pago in pagos:
            cursor.execute("""
                OPEN SYMMETRIC KEY ClaveEducacion DECRYPTION BY CERTIFICATE CertificadoEducacion;
                SELECT CONVERT(VARCHAR(100), DecryptByKey(Referencia_Pago))
                FROM Pagos WHERE Pagos_ID = %s;
                CLOSE SYMMETRIC KEY ClaveEducacion;
            """, [pago.pagos_id])
            row = cursor.fetchone()
            pago.referencia_descifrada = row[0] if row and row[0] else f'AUTO-{pago.pagos_id}'
    
    total_pagado = pagos.aggregate(total=Sum('monto'))['total'] or 0
    
    return render(request, 'Estudiante/mis_pagos.html', {
        'pagos': pagos,
        'total_pagado': total_pagado,
        'mensajes_no_leidos': Mensajes.objects.filter(receptor=usuario, leido=False).count()
    })

@login_required
def estudiante_cursos_disponibles(request):
    usuario = Usuarios.objects.get(email=request.user.username)
    estudiante = Estudiantes.objects.get(usuario=usuario)
    
    # Obtener grupos con cupo disponible
    grupos = Grupos.objects.filter(
        cupo_disponible__gt=0,
        curso__estado='Activo'
    ).select_related('curso', 'instructor')
    
    # Obtener grupos ya inscritos
    inscripciones = Inscripciones.objects.filter(estudiante=estudiante).values_list('grupo_id', flat=True)
    
    for grupo in grupos:
        grupo.ya_inscrito = grupo.grupo_id in inscripciones
    
    return render(request, 'Estudiante/cursos_disponibles.html', {'grupos_disponibles': grupos})

@login_required
def estudiante_inscribir(request):
    grupo_id = request.GET.get('grupo_id')
    if not grupo_id:
        return redirect('estudiante_cursos_disponibles')
    
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        grupo = Grupos.objects.get(grupo_id=grupo_id)
        estudiante = Estudiantes.objects.get(usuario=usuario)
        
        # Verificar si ya está inscrito
        if Inscripciones.objects.filter(estudiante=estudiante, grupo=grupo).exists():
            return redirect('estudiante_mis_cursos')
        
        # Verificar cupo
        if grupo.cupo_disponible <= 0:
            return redirect('estudiante_cursos_disponibles')
        
        # Establecer contexto de sesión ANTES de ejecutar el SP
        set_session_context(usuario.usuario_id)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                EXEC Registrar_Inscripcion %s, %s, %s
            """, (estudiante.estudiante_id, grupo_id, grupo.curso.costo))
        
    except Exception as e:
        print(f"Error al inscribir: {e}")
    
    return redirect('estudiante_mis_cursos')

@login_required
def estudiante_tareas(request, grupo_id):
    grupo = Grupos.objects.get(grupo_id=grupo_id)
    tareas = Tareas.objects.filter(grupo=grupo).order_by('-fecha_limite')
    
    usuario = Usuarios.objects.get(email=request.user.username)
    estudiante = Estudiantes.objects.get(usuario=usuario)
    inscripcion = Inscripciones.objects.get(estudiante=estudiante, grupo=grupo)
    
    tareas_con_entrega = []
    from datetime import date
    for tarea in tareas:
        entrega = Entregas.objects.filter(tarea=tarea, inscripcion=inscripcion).first()
        tareas_con_entrega.append({
            'tarea': tarea,
            'entrega': entrega,
            'vencida': tarea.fecha_limite < date.today() and not entrega
        })
    
    return render(request, 'Estudiante/tareas.html', {
        'grupo': grupo,
        'tareas_con_entrega': tareas_con_entrega
    })

@login_required
def estudiante_entregar_tarea(request, tarea_id):
    tarea = Tareas.objects.get(tarea_id=tarea_id)
    usuario = Usuarios.objects.get(email=request.user.username)
    estudiante = Estudiantes.objects.get(usuario=usuario)
    inscripcion = Inscripciones.objects.get(estudiante=estudiante, grupo=tarea.grupo)
    
    if request.method == 'POST':
        # Establecer contexto de sesión ANTES de guardar
        set_session_context(usuario.usuario_id)
        
        entrega, created = Entregas.objects.get_or_create(
            tarea=tarea,
            inscripcion=inscripcion,
            defaults={
                'comentario': request.POST.get('comentario', ''),
                'archivo': None
            }
        )
        if not created:
            entrega.comentario = request.POST.get('comentario', '')
            entrega.save()
        
        return redirect('estudiante_tareas', grupo_id=tarea.grupo.grupo_id)
    
    return render(request, 'Estudiante/entregar_tarea.html', {'tarea': tarea})

@login_required
def estudiante_ver_entrega(request, entrega_id):
    entrega = Entregas.objects.get(entrega_id=entrega_id)
    usuario = Usuarios.objects.get(email=request.user.username)
    estudiante = Estudiantes.objects.get(usuario=usuario)
    
    if entrega.inscripcion.estudiante != estudiante:
        return redirect('estudiante_dashboard')
    
    return render(request, 'Estudiante/ver_entrega.html', {'entrega': entrega})

# ============================================
# VISTAS DE INSTRUCTOR
# ============================================

@login_required
def instructor_dashboard(request):
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        instructor = Instructores.objects.get(usuario=usuario)
        nombre_completo = instructor.nombre + ' ' + instructor.apellidos
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
        
        # Estadísticas del instructor
        grupos = Grupos.objects.filter(instructor=instructor)
        total_grupos = grupos.count()
        total_estudiantes = Inscripciones.objects.filter(grupo__in=grupos).count()
        
        # Tareas por calificar
        tareas_por_calificar = Entregas.objects.filter(
            tarea__grupo__in=grupos,
            calificacion__isnull=True
        ).count()
        
    except (Usuarios.DoesNotExist, Instructores.DoesNotExist):
        nombre_completo = request.user.username
        mensajes_no_leidos = 0
        total_grupos = 0
        total_estudiantes = 0
        tareas_por_calificar = 0
    
    return render(request, 'Instructor/dashboard.html', {
        'nombre_instructor': nombre_completo,
        'mensajes_no_leidos': mensajes_no_leidos,
        'total_grupos': total_grupos,
        'total_estudiantes': total_estudiantes,
        'tareas_por_calificar': tareas_por_calificar
    })

@login_required
def instructor_mis_grupos(request):
    usuario = Usuarios.objects.get(email=request.user.username)
    instructor = Instructores.objects.get(usuario=usuario)
    grupos = Grupos.objects.filter(instructor=instructor).select_related('curso')
    
    for grupo in grupos:
        grupo.inscripciones_count = Inscripciones.objects.filter(grupo=grupo).count()
    
    return render(request, 'Instructor/mis_grupos.html', {'grupos': grupos})

@login_required
def instructor_gestionar_evaluaciones(request):
    usuario = Usuarios.objects.get(email=request.user.username)
    instructor = Instructores.objects.get(usuario=usuario)
    grupo_id = request.GET.get('grupo_id')
    
    if not grupo_id:
        grupos = Grupos.objects.filter(instructor=instructor).select_related('curso')
        for grupo in grupos:
            grupo.inscripciones_count = Inscripciones.objects.filter(grupo=grupo).count()
        return render(request, 'Instructor/seleccionar_grupo.html', {'grupos': grupos})
    
    try:
        grupo = Grupos.objects.get(grupo_id=grupo_id, instructor=instructor)
    except Grupos.DoesNotExist:
        return redirect('instructor_mis_grupos')
    
    inscripciones = Inscripciones.objects.filter(grupo=grupo).select_related('estudiante')
    
    estudiantes_con_evaluacion = []
    for inscripcion in inscripciones:
        evaluacion = Evaluaciones.objects.filter(inscripcion=inscripcion).first()
        estudiantes_con_evaluacion.append({
            'estudiante': inscripcion.estudiante,
            'inscripcion': inscripcion,
            'evaluacion': evaluacion
        })
    
    return render(request, 'Instructor/gestionar_evaluaciones.html', {
        'grupo_actual': grupo,
        'estudiantes_con_evaluacion': estudiantes_con_evaluacion
    })

@login_required
def instructor_registrar_evaluacion(request):
    if request.method == 'POST':
        inscripcion_id = request.POST.get('inscripcion_id')
        calificacion = request.POST.get('calificacion')
        comentario = request.POST.get('comentario', '')
        grupo_id = request.POST.get('grupo_id') or request.GET.get('grupo_id')
        
        try:
            usuario = Usuarios.objects.get(email=request.user.username)
            
            # Establecer contexto de sesión
            set_session_context(usuario.usuario_id)
            
            # Buscar evaluación existente para esta inscripción
            evaluacion_existente = Evaluaciones.objects.filter(inscripcion_id=inscripcion_id).first()
            
            if evaluacion_existente:
                # ACTUALIZAR evaluación existente (NO crear nueva)
                evaluacion_existente.calificacion = calificacion
                if comentario:
                    evaluacion_existente.comentarios = comentario.encode('utf-8')
                evaluacion_existente.fecha = datetime.date.today()
                evaluacion_existente.save()
                print(f"Evaluación ACTUALIZADA para inscripción {inscripcion_id}")
            else:
                # CREAR nueva evaluación solo si no existe
                Evaluaciones.objects.create(
                    inscripcion_id=inscripcion_id,
                    calificacion=calificacion,
                    comentarios=comentario.encode('utf-8') if comentario else None
                )
                print(f"Evaluación CREADA para inscripción {inscripcion_id}")
            
            # Redirigir de vuelta al grupo
            if grupo_id:
                return redirect(f'/instructor-gestionar-evaluaciones/?grupo_id={grupo_id}')
            else:
                return redirect('instructor_gestionar_evaluaciones')
            
        except Exception as e:
            print(f"Error al registrar evaluación: {e}")
    
    return redirect('instructor_gestionar_evaluaciones')

@login_required
def instructor_tareas(request, grupo_id):
    grupo = Grupos.objects.get(grupo_id=grupo_id)
    tareas = Tareas.objects.filter(grupo=grupo).order_by('-fecha_creacion')
    
    # Contar entregas por tarea
    for tarea in tareas:
        tarea.total_entregas = Entregas.objects.filter(tarea=tarea).count()
        tarea.entregas_calificadas = Entregas.objects.filter(tarea=tarea, calificacion__isnull=False).count()
    
    return render(request, 'Instructor/tareas.html', {'grupo': grupo, 'tareas': tareas})

@login_required
def instructor_crear_tarea(request, grupo_id):
    grupo = Grupos.objects.get(grupo_id=grupo_id)
    usuario = Usuarios.objects.get(email=request.user.username)
    
    if request.method == 'POST':
        # Establecer contexto de sesión ANTES de crear la tarea
        set_session_context(usuario.usuario_id)
        
        Tareas.objects.create(
            grupo=grupo,
            titulo=request.POST.get('titulo'),
            descripcion=request.POST.get('descripcion'),
            fecha_limite=request.POST.get('fecha_limite'),
            puntaje_maximo=request.POST.get('puntaje_maximo'),
            creado_por=usuario
        )
        return redirect('instructor_tareas', grupo_id=grupo_id)
    
    return render(request, 'Instructor/crear_tarea.html', {'grupo': grupo})

@login_required
def instructor_entregas_tarea(request, tarea_id):
    try:
        tarea = Tareas.objects.get(tarea_id=tarea_id)
    except Tareas.DoesNotExist:
        return redirect('instructor_mis_grupos')
    
    entregas = Entregas.objects.filter(tarea=tarea).select_related('inscripcion__estudiante__usuario')
    
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
    except:
        mensajes_no_leidos = 0
    
    return render(request, 'Instructor/entregas_tarea.html', {
        'tarea': tarea,
        'entregas': entregas,
        'mensajes_no_leidos': mensajes_no_leidos
    })

@login_required
def instructor_calificar_entrega(request, entrega_id):
    try:
        entrega = Entregas.objects.get(entrega_id=entrega_id)
    except Entregas.DoesNotExist:
        # Crear un objeto dummy para mostrar el mensaje
        from types import SimpleNamespace
        entrega = SimpleNamespace()
        entrega.no_existe = True
        return render(request, 'Instructor/calificar_entrega.html', {'entrega': entrega})
    
    if request.method == 'POST':
        usuario = Usuarios.objects.get(email=request.user.username)
        
        # Establecer contexto de sesión ANTES de guardar
        set_session_context(usuario.usuario_id)
        
        entrega.calificacion = request.POST.get('calificacion')
        entrega.comentario_instructor = request.POST.get('comentario_instructor')
        entrega.save()
        
        return redirect('instructor_entregas_tarea', tarea_id=entrega.tarea.tarea_id)
    
    return render(request, 'Instructor/calificar_entrega.html', {'entrega': entrega})

# ============================================
# VISTAS DE ADMINISTRADOR
# ============================================

@login_required
def admin_dashboard(request):
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        nombre_admin = usuario.email
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
    except Usuarios.DoesNotExist:
        nombre_admin = request.user.username
        mensajes_no_leidos = 0
    
    # Estadísticas generales
    total_cursos = Cursos.objects.count()
    total_estudiantes = Estudiantes.objects.count()
    total_instructores = Instructores.objects.count()
    total_inscripciones = Inscripciones.objects.count()
    total_grupos = Grupos.objects.count()
    ingresos_totales = Pagos.objects.aggregate(total=Sum('monto'))['total'] or 0
    
    # Cursos más populares
    cursos_populares = Cursos.objects.annotate(
        total_inscripciones=Count('grupos__inscripciones')
    ).order_by('-total_inscripciones')[:5]
    
    return render(request, 'Administrador/dashboard.html', {
        'nombre_admin': nombre_admin,
        'total_cursos': total_cursos,
        'total_estudiantes': total_estudiantes,
        'total_instructores': total_instructores,
        'total_inscripciones': total_inscripciones,
        'total_grupos': total_grupos,
        'ingresos_totales': ingresos_totales,
        'cursos_populares': cursos_populares,
        'mensajes_no_leidos': mensajes_no_leidos
    })

# ============================================
# ADMINISTRADOR - CURSOS
# ============================================

@login_required
def admin_gestionar_cursos(request):
    categoria = request.GET.get('categoria')
    
    if categoria == 'Programacion':
        cursos = Cursos_Programacion.objects.all()
    elif categoria == 'Redes':
        cursos = Cursos_Redes.objects.all()
    elif categoria == 'Ciberseguridad':
        cursos = Cursos_Ciberseguridad.objects.all()
    elif categoria == 'Otra':
        cursos = Cursos_Otra.objects.all()
    else:
        cursos = Cursos.objects.all()
    
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
    except:
        mensajes_no_leidos = 0
    
    return render(request, 'Administrador/Admin_Cursos/gestionar_cursos.html', {
        'cursos': cursos,
        'categoria_seleccionada': categoria,
        'mensajes_no_leidos': mensajes_no_leidos
    })

@login_required
def admin_crear_curso(request):
    if request.method == 'POST':
        admin_usuario = Usuarios.objects.get(email=request.user.username)
        
        # Establecer contexto de sesión ANTES de crear
        set_session_context(admin_usuario.usuario_id)
        
        nombre_curso = request.POST.get('nombre_curso')
        categoria = request.POST.get('categoria', '')
        duracion_horas = request.POST.get('duracion_horas')
        costo = request.POST.get('costo')
        estado = request.POST.get('estado', 'Activo')
        
        Cursos.objects.create(
            nombre_curso=nombre_curso,
            categoria=categoria if categoria else None,
            duracion_horas=duracion_horas if duracion_horas else None,
            costo=costo,
            estado=estado
        )
        return redirect('admin_gestionar_cursos')
    
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
    except:
        mensajes_no_leidos = 0
    
    return render(request, 'Administrador/Admin_Cursos/crear_curso.html', {
        'mensajes_no_leidos': mensajes_no_leidos
    })

@login_required
def admin_editar_curso(request, curso_id):
    curso = Cursos.objects.get(curso_id=curso_id)
    
    if request.method == 'POST':
        admin_usuario = Usuarios.objects.get(email=request.user.username)
        
        set_session_context(admin_usuario.usuario_id)
        
        curso.nombre_curso = request.POST.get('nombre_curso')
        curso.categoria = request.POST.get('categoria', '') or None
        curso.duracion_horas = request.POST.get('duracion_horas') or None
        curso.costo = request.POST.get('costo')
        curso.estado = request.POST.get('estado')
        curso.save()
        
        return redirect('admin_gestionar_cursos')
    
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
    except:
        mensajes_no_leidos = 0
    
    return render(request, 'Administrador/Admin_Cursos/editar_curso.html', {
        'curso': curso,
        'mensajes_no_leidos': mensajes_no_leidos
    })

@login_required
def admin_ver_curso(request, curso_id):
    curso = Cursos.objects.get(curso_id=curso_id)
    grupos = Grupos.objects.filter(curso=curso).select_related('instructor')
    
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
    except:
        mensajes_no_leidos = 0
    
    return render(request, 'Administrador/Admin_Cursos/ver_detalle.html', {
        'curso': curso,
        'grupos': grupos,
        'mensajes_no_leidos': mensajes_no_leidos
    })

@login_required
def admin_eliminar_curso(request, curso_id):
    curso = Cursos.objects.get(curso_id=curso_id)
    
    admin_usuario = Usuarios.objects.get(email=request.user.username)
    set_session_context(admin_usuario.usuario_id)
    
    curso.delete()
    
    return redirect('admin_gestionar_cursos')


# ============================================
# ADMINISTRADOR - GRUPOS
# ============================================

@login_required
def admin_gestionar_grupos(request):
    estado = request.GET.get('estado')
    
    if estado == 'disponible':
        grupos = Grupos_Disponibles.objects.all().select_related('curso', 'instructor')
    elif estado == 'lleno':
        grupos = Grupos_Llenos.objects.all().select_related('curso', 'instructor')
    else:
        grupos = Grupos.objects.all().select_related('curso', 'instructor')
    
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
    except:
        mensajes_no_leidos = 0
    
    return render(request, 'Administrador/Admin_Grupos/gestionar_grupos.html', {
        'grupos': grupos,
        'estado_seleccionado': estado,
        'mensajes_no_leidos': mensajes_no_leidos
    })

@login_required
def admin_crear_grupo(request):
    if request.method == 'POST':
        admin_usuario = Usuarios.objects.get(email=request.user.username)
        
        set_session_context(admin_usuario.usuario_id)
        
        curso_id = request.POST.get('curso_id')
        instructor_id = request.POST.get('instructor_id')
        cupo_maximo = request.POST.get('cupo_maximo')
        fecha_inicio = request.POST.get('fecha_inicio')
        
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO Grupos (Curso_ID, Instructor_ID, Cupo_Maximo, Cupo_Disponible, Fecha_Inicio)
                VALUES (%s, %s, %s, %s, %s)
            """, [curso_id, instructor_id, cupo_maximo, cupo_maximo, fecha_inicio])
        
        return redirect('admin_gestionar_grupos')
    
    cursos = Cursos.objects.filter(estado='Activo')
    instructores = Instructores.objects.filter(estado='Activo')
    
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
    except:
        mensajes_no_leidos = 0
    
    return render(request, 'Administrador/Admin_Grupos/crear_grupo.html', {
        'cursos': cursos,
        'instructores': instructores,
        'mensajes_no_leidos': mensajes_no_leidos
    })

@login_required
def admin_editar_grupo(request, grupo_id):
    grupo = Grupos.objects.get(grupo_id=grupo_id)
    
    if request.method == 'POST':
        admin_usuario = Usuarios.objects.get(email=request.user.username)
        
        set_session_context(admin_usuario.usuario_id)
        
        grupo.curso_id = request.POST.get('curso_id')
        grupo.instructor_id = request.POST.get('instructor_id')
        grupo.cupo_maximo = request.POST.get('cupo_maximo')
        grupo.cupo_disponible = request.POST.get('cupo_disponible')
        grupo.fecha_inicio = request.POST.get('fecha_inicio')
        grupo.save()
        
        return redirect('admin_gestionar_grupos')
    
    cursos = Cursos.objects.filter(estado='Activo')
    instructores = Instructores.objects.filter(estado='Activo')
    
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
    except:
        mensajes_no_leidos = 0
    
    return render(request, 'Administrador/Admin_Grupos/editar_grupo.html', {
        'grupo': grupo,
        'cursos': cursos,
        'instructores': instructores,
        'mensajes_no_leidos': mensajes_no_leidos
    })

@login_required
def admin_ver_grupo(request, grupo_id):
    grupo = Grupos.objects.get(grupo_id=grupo_id)
    inscripciones = Inscripciones.objects.filter(grupo=grupo).select_related('estudiante__usuario')
    
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
    except:
        mensajes_no_leidos = 0
    
    return render(request, 'Administrador/Admin_Grupos/ver_detalle.html', {
        'grupo': grupo,
        'inscripciones': inscripciones,
        'mensajes_no_leidos': mensajes_no_leidos
    })

@login_required
def admin_eliminar_grupo(request, grupo_id):
    grupo = Grupos.objects.get(grupo_id=grupo_id)
    
    admin_usuario = Usuarios.objects.get(email=request.user.username)
    set_session_context(admin_usuario.usuario_id)
    
    grupo.delete()
    
    return redirect('admin_gestionar_grupos')

# ============================================
# ADMINISTRADOR - INSTRUCTORES
# ============================================

@login_required
def admin_gestionar_instructores(request):
    especialidad = request.GET.get('especialidad')
    
    if especialidad == 'TI':
        instructores = Instructores_TI.objects.all().select_related('usuario')
    elif especialidad == 'Redes':
        instructores = Instructores_Redes.objects.all().select_related('usuario')
    elif especialidad == 'Otra':
        instructores = Instructores_Otra.objects.all().select_related('usuario')
    else:
        instructores = Instructores.objects.all().select_related('usuario')
    
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
    except:
        mensajes_no_leidos = 0
    
    return render(request, 'Administrador/Admin_Instructores/gestionar_instructores.html', {
        'instructores': instructores,
        'especialidad_seleccionada': especialidad,
        'mensajes_no_leidos': mensajes_no_leidos
    })

@login_required
def admin_crear_instructor(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        nombre = request.POST.get('nombre')
        apellidos = request.POST.get('apellidos')
        especialidad = request.POST.get('especialidad', '')
        cedula_profesional = request.POST.get('cedula_profesional')
        estado = request.POST.get('estado', 'Activo')
        
        # Verificar si el email ya existe en Django User o en tabla Usuarios
        if User.objects.filter(username=email).exists() or Usuarios.objects.filter(email=email).exists():
            try:
                usuario = Usuarios.objects.get(email=request.user.username)
                mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
            except:
                mensajes_no_leidos = 0
            
            return render(request, 'Administrador/Admin_Instructores/crear_instructor.html', {
                'error': f'El email {email} ya está registrado en el sistema.',
                'mensajes_no_leidos': mensajes_no_leidos
            })
        
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password
                )
                user.save()
                
                admin_usuario = Usuarios.objects.get(email=request.user.username)
                
                set_session_context(admin_usuario.usuario_id)
                
                with connection.cursor() as cursor:
                    cursor.execute("""
                        EXEC Registrar_Instructor %s, %s, %s, %s, %s, %s, %s
                    """, (email, password, nombre, apellidos, especialidad, cedula_profesional, estado))
                
                return redirect('admin_gestionar_instructores')
                
        except Exception as e:
            try:
                usuario = Usuarios.objects.get(email=request.user.username)
                mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
            except:
                mensajes_no_leidos = 0
            
            return render(request, 'Administrador/Admin_Instructores/crear_instructor.html', {
                'error': str(e),
                'mensajes_no_leidos': mensajes_no_leidos
            })
    
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
    except:
        mensajes_no_leidos = 0
    
    return render(request, 'Administrador/Admin_Instructores/crear_instructor.html', {
        'mensajes_no_leidos': mensajes_no_leidos
    })

@login_required
def admin_editar_instructor(request, instructor_id):
    instructor = Instructores.objects.get(instructor_id=instructor_id)
    
    if request.method == 'POST':
        admin_usuario = Usuarios.objects.get(email=request.user.username)
        
        set_session_context(admin_usuario.usuario_id)
        
        instructor.nombre = request.POST.get('nombre')
        instructor.apellidos = request.POST.get('apellidos')
        instructor.especialidad = request.POST.get('especialidad', '')
        instructor.estado = request.POST.get('estado')
        instructor.save()
        
        return redirect('admin_gestionar_instructores')
    
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
    except:
        mensajes_no_leidos = 0
    
    return render(request, 'Administrador/Admin_Instructores/editar_instructor.html', {
        'instructor': instructor,
        'mensajes_no_leidos': mensajes_no_leidos
    })

@login_required
def admin_ver_instructor(request, instructor_id):
    instructor = Instructores.objects.get(instructor_id=instructor_id)
    
    # Descifrar cédula profesional usando conexión directa
    cedula_descifrada = None
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={settings.DATABASES['default']['HOST']};"
            f"DATABASE={settings.DATABASES['default']['NAME']};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
        )
        cursor = conn.cursor()
        cursor.execute("""
            OPEN SYMMETRIC KEY ClaveEducacion DECRYPTION BY CERTIFICATE CertificadoEducacion;
            SELECT CONVERT(VARCHAR(100), DecryptByKey(Cedula_Profesional))
            FROM Instructores WHERE Instructor_ID = ?;
            CLOSE SYMMETRIC KEY ClaveEducacion;
        """, instructor_id)
        row = cursor.fetchone()
        if row:
            cedula_descifrada = row[0]
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error al descifrar cédula: {e}")
    
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
    except:
        mensajes_no_leidos = 0
    
    return render(request, 'Administrador/Admin_Instructores/ver_detalle.html', {
        'instructor': instructor,
        'cedula_descifrada': cedula_descifrada,
        'mensajes_no_leidos': mensajes_no_leidos
    })

@login_required
def admin_eliminar_instructor(request, instructor_id):
    instructor = Instructores.objects.get(instructor_id=instructor_id)
    usuario = instructor.usuario
    
    # Eliminar de auth_user si existe
    try:
        auth_user = User.objects.filter(
            Q(username=usuario.email) | Q(email=usuario.email)
        ).first()
        if auth_user:
            auth_user.delete()
    except Exception:
        pass
    
    admin_usuario = Usuarios.objects.get(email=request.user.username)
    set_session_context(admin_usuario.usuario_id)
    
    instructor.delete()  # CASCADE elimina de Usuarios
    
    return redirect('admin_gestionar_instructores')
# ============================================
# ADMINISTRADOR - ESTUDIANTES
# ============================================

@login_required
def admin_gestionar_estudiantes(request):
    tipo = request.GET.get('tipo_documento')
    
    if tipo == 'INE':
        estudiantes = Estudiantes_INE.objects.all().select_related('usuario')
    elif tipo == 'Pasaporte':
        estudiantes = Estudiantes_Pasaporte.objects.all().select_related('usuario')
    else:
        estudiantes = Estudiantes.objects.all().select_related('usuario')
    
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
    except:
        mensajes_no_leidos = 0
    
    return render(request, 'Administrador/Admin_Estudiante/gestionar_estudiantes.html', {
        'estudiantes': estudiantes,
        'tipo_seleccionado': tipo,
        'mensajes_no_leidos': mensajes_no_leidos
    })

@login_required
def admin_crear_estudiante(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        nombre = request.POST.get('nombre')
        apellidos = request.POST.get('apellidos')
        direccion = request.POST.get('direccion', '')
        telefono = request.POST.get('telefono', '')
        tipo_doc = request.POST.get('tipo_doc')
        num_doc = request.POST.get('num_doc')
        
        # Verificar si el email ya existe
        if User.objects.filter(username=email).exists() or Usuarios.objects.filter(email=email).exists():
            try:
                usuario = Usuarios.objects.get(email=request.user.username)
                mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
            except:
                mensajes_no_leidos = 0
            
            return render(request, 'Administrador/Admin_Estudiante/crear_estudiante.html', {
                'error': f'El email {email} ya está registrado en el sistema.',
                'mensajes_no_leidos': mensajes_no_leidos
            })
        
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password
                )
                user.save()
                
                admin_usuario = Usuarios.objects.get(email=request.user.username)
                
                set_session_context(admin_usuario.usuario_id)
                
                with connection.cursor() as cursor:
                    cursor.execute("""
                        EXEC Registrar_Estudiante %s, %s, %s, %s, %s, %s, %s, %s
                    """, (email, password, nombre, apellidos, direccion, telefono, tipo_doc, num_doc))
                
                return redirect('admin_gestionar_estudiantes')
                
        except Exception as e:
            try:
                usuario = Usuarios.objects.get(email=request.user.username)
                mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
            except:
                mensajes_no_leidos = 0
            
            return render(request, 'Administrador/Admin_Estudiante/crear_estudiante.html', {
                'error': str(e),
                'mensajes_no_leidos': mensajes_no_leidos
            })
    
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
    except:
        mensajes_no_leidos = 0
    
    return render(request, 'Administrador/Admin_Estudiante/crear_estudiante.html', {
        'mensajes_no_leidos': mensajes_no_leidos
    })

@login_required
def admin_editar_estudiante(request, estudiante_id):
    estudiante = Estudiantes.objects.get(estudiante_id=estudiante_id)
    
    if request.method == 'POST':
        admin_usuario = Usuarios.objects.get(email=request.user.username)
        
        set_session_context(admin_usuario.usuario_id)
        
        estudiante.nombre = request.POST.get('nombre')
        estudiante.apellidos = request.POST.get('apellidos')
        estudiante.direccion = request.POST.get('direccion', '')
        estudiante.telefono = request.POST.get('telefono', '')
        estudiante.tipo_documento = request.POST.get('tipo_doc')
        estudiante.save()
        
        return redirect('admin_gestionar_estudiantes')
    
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
    except:
        mensajes_no_leidos = 0
    
    return render(request, 'Administrador/Admin_Estudiante/editar_estudiante.html', {
        'estudiante': estudiante,
        'mensajes_no_leidos': mensajes_no_leidos
    })

@login_required
def admin_ver_estudiante(request, estudiante_id):
    estudiante = Estudiantes.objects.get(estudiante_id=estudiante_id)
    
    # Descifrar documento usando conexión directa
    documento_descifrado = None
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={settings.DATABASES['default']['HOST']};"
            f"DATABASE={settings.DATABASES['default']['NAME']};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
        )
        cursor = conn.cursor()
        cursor.execute("""
            OPEN SYMMETRIC KEY ClaveEducacion DECRYPTION BY CERTIFICATE CertificadoEducacion;
            SELECT CONVERT(VARCHAR(50), DecryptByKey(Numero_Documento))
            FROM Estudiantes WHERE Estudiante_ID = ?;
            CLOSE SYMMETRIC KEY ClaveEducacion;
        """, estudiante_id)
        row = cursor.fetchone()
        if row:
            documento_descifrado = row[0]
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error al descifrar: {e}")
    
    # Obtener inscripciones del estudiante
    inscripciones = Inscripciones.objects.filter(estudiante=estudiante).select_related('grupo__curso')
    
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
    except:
        mensajes_no_leidos = 0
    
    return render(request, 'Administrador/Admin_Estudiante/ver_detalle.html', {
        'estudiante': estudiante,
        'documento_descifrado': documento_descifrado,
        'inscripciones': inscripciones,
        'mensajes_no_leidos': mensajes_no_leidos
    })

@login_required
def admin_eliminar_estudiante(request, estudiante_id):
    estudiante = Estudiantes.objects.get(estudiante_id=estudiante_id)
    usuario = estudiante.usuario
    
    # Eliminar de auth_user si existe
    try:
        auth_user = User.objects.filter(
            Q(username=usuario.email) | Q(email=usuario.email)
        ).first()
        if auth_user:
            auth_user.delete()
    except Exception:
        pass
    
    admin_usuario = Usuarios.objects.get(email=request.user.username)
    set_session_context(admin_usuario.usuario_id)
    
    estudiante.delete()  # CASCADE elimina de Usuarios
    
    return redirect('admin_gestionar_estudiantes')
# ============================================
# ADMINISTRADOR - REPORTES Y AUDITORÍAS
# ============================================
@login_required
def admin_reportes(request):
    # Ranking de cursos más demandados
    cursos_ranking = Cursos.objects.annotate(
        total_inscripciones=Count('grupos__inscripciones'),
        ingresos_totales=Sum('grupos__inscripciones__pagos__monto')
    ).order_by('-total_inscripciones')
    
    for idx, curso in enumerate(cursos_ranking, 1):
        curso.ranking = idx
    
    # Obtener datos del PIVOT desde la tabla Inscripciones_Pivot
    inscripciones_pivot = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM Inscripciones_Pivot ORDER BY Anio")
            rows = cursor.fetchall()
            for row in rows:
                inscripciones_pivot.append({
                    'anio': row[0],
                    'Enero': row[1] or 0,
                    'Febrero': row[2] or 0,
                    'Marzo': row[3] or 0,
                    'Abril': row[4] or 0,
                    'Mayo': row[5] or 0,
                    'Junio': row[6] or 0,
                    'Julio': row[7] or 0,
                    'Agosto': row[8] or 0,
                    'Septiembre': row[9] or 0,
                    'Octubre': row[10] or 0,
                    'Noviembre': row[11] or 0,
                    'Diciembre': row[12] or 0,
                })
    except Exception as e:
        print(f"Error al obtener datos del PIVOT: {e}")
        inscripciones_pivot = []
    
    # Pagos por mes (formato plano, puedes mantenerlo o también hacer PIVOT)
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    YEAR(Fecha_Pago) AS Anio,
                    MONTH(Fecha_Pago) AS Mes,
                    SUM(Monto) AS Total
                FROM Pagos
                GROUP BY YEAR(Fecha_Pago), MONTH(Fecha_Pago)
                ORDER BY Anio, Mes
            """)
            pagos_mensuales = cursor.fetchall()
    except:
        pagos_mensuales = []
    
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
    except:
        mensajes_no_leidos = 0
    
    return render(request, 'Administrador/reportes.html', {
        'cursos_ranking': cursos_ranking,
        'inscripciones_pivot': inscripciones_pivot,
        'pagos_mensuales': pagos_mensuales,
        'mensajes_no_leidos': mensajes_no_leidos
    })

@login_required
def admin_auditorias(request):
    auditoria_inscripciones = Auditoria_Inscripciones.objects.all().order_by('-fecha_evento')[:100]
    auditoria_evaluaciones = Auditoria_Evaluaciones.objects.all().order_by('-fecha_evento')[:100]
    auditoria_pagos = Auditoria_Pagos.objects.all().order_by('-fecha_evento')[:100]
    auditoria_estudiantes = Auditoria_Estudiantes.objects.all().order_by('-fecha_evento')[:100]
    auditoria_entregas = Auditoria_Entregas.objects.all().order_by('-fecha_evento')[:100]
    auditoria_instructores = Auditoria_Instructores.objects.all().order_by('-fecha_evento')[:100]
    auditoria_cursos = Auditoria_Cursos.objects.all().order_by('-fecha_evento')[:100]
    auditoria_grupos = Auditoria_Grupos.objects.all().order_by('-fecha_evento')[:100]
    
    try:
        usuario = Usuarios.objects.get(email=request.user.username)
        mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario, leido=False).count()
    except:
        mensajes_no_leidos = 0
    
    return render(request, 'Administrador/auditorias.html', {
        'auditoria_inscripciones': auditoria_inscripciones,
        'auditoria_evaluaciones': auditoria_evaluaciones,
        'auditoria_pagos': auditoria_pagos,
        'auditoria_estudiantes': auditoria_estudiantes,
        'auditoria_entregas': auditoria_entregas,
        'auditoria_instructores': auditoria_instructores,
        'auditoria_cursos': auditoria_cursos,
        'auditoria_grupos': auditoria_grupos,
        'mensajes_no_leidos': mensajes_no_leidos
    })

# ============================================
# VISTAS DE MENSAJES
# ============================================

@login_required
def mensajes(request):
    usuario = Usuarios.objects.get(email=request.user.username)
    
    recibidos = Mensajes.objects.filter(receptor=usuario).order_by('-fecha_envio')
    enviados = Mensajes.objects.filter(emisor=usuario).order_by('-fecha_envio')
    mensajes_no_leidos = recibidos.filter(leido=False).count()
    
    rol = 'estudiante'
    if usuario.rol.rol_id == 1:
        rol = 'admin'
    elif usuario.rol.rol_id == 2:
        rol = 'instructor'
    
    # Paginación
    paginator_recibidos = Paginator(recibidos, 20)
    paginator_enviados = Paginator(enviados, 20)
    
    page_recibidos = request.GET.get('page_recibidos', 1)
    page_enviados = request.GET.get('page_enviados', 1)
    
    recibidos_page = paginator_recibidos.get_page(page_recibidos)
    enviados_page = paginator_enviados.get_page(page_enviados)
    
    return render(request, 'mensajes.html', {
        'recibidos': recibidos_page,
        'enviados': enviados_page,
        'mensajes_no_leidos': mensajes_no_leidos,
        'rol': rol
    })

@login_required
def enviar_mensaje(request):
    usuario_actual = Usuarios.objects.get(email=request.user.username)
    
    responder_a_id = request.GET.get('responder_a')
    asunto_predefinido = request.GET.get('asunto', '')
    tarea_id_predefinida = request.GET.get('tarea_id')
    
    if request.method == 'POST':
        receptor = Usuarios.objects.get(usuario_id=request.POST.get('receptor_id'))
        
        set_session_context(usuario_actual.usuario_id)
        
        Mensajes.objects.create(
            emisor=usuario_actual,
            receptor=receptor,
            asunto=request.POST.get('asunto'),
            contenido=request.POST.get('contenido'),
            tarea_id=request.POST.get('tarea_id') or None
        )
        
        return redirect('mensajes')
    
    # Obtener usuarios según el rol
    if usuario_actual.rol.rol_id == 1:  # Admin puede enviar a todos
        usuarios = Usuarios.objects.exclude(usuario_id=usuario_actual.usuario_id).select_related('rol')
    elif usuario_actual.rol.rol_id == 2:  # Instructor puede enviar a sus estudiantes
        grupos = Grupos.objects.filter(instructor__usuario=usuario_actual)
        estudiantes_ids = Inscripciones.objects.filter(grupo__in=grupos).values_list('estudiante__usuario_id', flat=True).distinct()
        usuarios = Usuarios.objects.filter(usuario_id__in=estudiantes_ids).exclude(usuario_id=usuario_actual.usuario_id).select_related('rol')
    else:  # Estudiante puede enviar a sus instructores
        inscripciones = Inscripciones.objects.filter(estudiante__usuario=usuario_actual)
        instructores_ids = inscripciones.values_list('grupo__instructor__usuario_id', flat=True).distinct()
        usuarios = Usuarios.objects.filter(usuario_id__in=instructores_ids).exclude(usuario_id=usuario_actual.usuario_id).select_related('rol')
    
    if responder_a_id:
        try:
            destinatario = Usuarios.objects.get(usuario_id=responder_a_id)
            if destinatario in usuarios:
                destinatario_preseleccionado = destinatario
            else:
                destinatario_preseleccionado = None
        except Usuarios.DoesNotExist:
            destinatario_preseleccionado = None
    else:
        destinatario_preseleccionado = None
    
    # Tareas para referencia - CORREGIDO (evita DISTINCT sobre campos TEXT)
    if usuario_actual.rol.rol_id == 2:
        # Instructor: tareas de sus grupos
        tareas_ids = Tareas.objects.filter(grupo__instructor__usuario=usuario_actual).values_list('tarea_id', flat=True)
        tareas = Tareas.objects.filter(tarea_id__in=tareas_ids)
    else:
        # Estudiante: tareas de sus grupos
        tareas_ids = Tareas.objects.filter(grupo__inscripciones__estudiante__usuario=usuario_actual).values_list('tarea_id', flat=True).distinct()
        tareas = Tareas.objects.filter(tarea_id__in=tareas_ids)
    
    rol = 'estudiante'
    if usuario_actual.rol.rol_id == 1:
        rol = 'admin'
    elif usuario_actual.rol.rol_id == 2:
        rol = 'instructor'
    
    mensajes_no_leidos = Mensajes.objects.filter(receptor=usuario_actual, leido=False).count()
    
    return render(request, 'enviar_mensaje.html', {
        'usuarios': usuarios,
        'tareas': tareas,
        'rol': rol,
        'mensajes_no_leidos': mensajes_no_leidos,
        'destinatario_preseleccionado': destinatario_preseleccionado,
        'asunto_preseleccionado': asunto_predefinido,
        'tarea_id_predefinida': tarea_id_predefinida
    })

@login_required
def ver_mensaje(request, mensaje_id):
    mensaje = Mensajes.objects.get(mensaje_id=mensaje_id)
    
    usuario_actual = Usuarios.objects.get(email=request.user.username)
    if mensaje.receptor == usuario_actual and not mensaje.leido:
        mensaje.leido = True
        mensaje.save()
    
    return render(request, 'ver_mensaje.html', {'mensaje': mensaje})

@login_required
def responder_mensaje(request, mensaje_id):
    mensaje_original = Mensajes.objects.get(mensaje_id=mensaje_id)
    return redirect(f"{reverse('enviar_mensaje')}?responder_a={mensaje_original.emisor.usuario_id}&asunto=RE: {mensaje_original.asunto}")