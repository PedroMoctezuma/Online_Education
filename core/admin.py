from django import forms
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import connection
from django.db.models import Avg, Count, Sum, F, Q
from django.utils.html import format_html

from .models import *

# ======================================================
# FORMULARIOS PERSONALIZADOS CON LÓGICA CREAR/EDITAR
# ======================================================

class InstructorForm(forms.ModelForm):
    email = forms.EmailField(label='Correo Electrónico', required=True)
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput, required=True)
    cedula_profesional_texto = forms.CharField(label='Cédula Profesional', required=True, widget=forms.TextInput(attrs={'placeholder': 'Ej: 12345678'}))
    
    class Meta:
        model = Instructores
        fields = ('nombre', 'apellidos', 'especialidad', 'estado')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # EDITAR: quitar campos que NO se pueden editar
            self.fields.pop('email', None)
            self.fields.pop('password', None)
            self.fields.pop('cedula_profesional_texto', None)
            # Los campos editables son: nombre, apellidos, especialidad, estado
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        with connection.cursor() as cursor:
            if self.instance.pk:  # EDITAR - solo UPDATE de campos NO cifrados
                cursor.execute("""
                    UPDATE Instructores 
                    SET Nombre = %s, Apellidos = %s, Especialidad = %s, Estado = %s
                    WHERE Instructor_ID = %s
                """, [
                    instance.nombre, instance.apellidos, 
                    instance.especialidad or '', instance.estado, 
                    self.instance.pk
                ])
                return instance
            else:  # CREAR - INSERT usando SP (cifra los datos)
                cursor.execute("""
                    EXEC Registrar_Instructor %s, %s, %s, %s, %s, %s, %s
                """, [
                    self.cleaned_data['email'],
                    self.cleaned_data['password'],
                    instance.nombre,
                    instance.apellidos,
                    instance.especialidad or '',
                    self.cleaned_data['cedula_profesional_texto'],
                    instance.estado
                ])
                usuario = Usuarios.objects.get(email=self.cleaned_data['email'])
                instructor = Instructores.objects.get(usuario=usuario)
                return instructor
    
    def save_m2m(self):
        pass


class EstudianteForm(forms.ModelForm):
    email = forms.EmailField(label='Correo Electrónico', required=True)
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput, required=True)
    numero_documento_texto = forms.CharField(label='Número de Documento', required=True)
    
    class Meta:
        model = Estudiantes
        fields = ('nombre', 'apellidos', 'direccion', 'telefono', 'tipo_documento')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # EDITAR: quitar campos que NO se pueden editar
            self.fields.pop('email', None)
            self.fields.pop('password', None)
            self.fields.pop('numero_documento_texto', None)
            # Los campos editables son: nombre, apellidos, direccion, telefono, tipo_documento
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        with connection.cursor() as cursor:
            if self.instance.pk:  # EDITAR - solo UPDATE de campos NO cifrados
                cursor.execute("""
                    UPDATE Estudiantes 
                    SET Nombre = %s, Apellidos = %s, Direccion = %s, 
                        Telefono = %s, Tipo_Documento = %s
                    WHERE Estudiante_ID = %s
                """, [
                    instance.nombre, instance.apellidos, 
                    instance.direccion or '', instance.telefono or '', 
                    instance.tipo_documento or '', self.instance.pk
                ])
                return instance
            else:  # CREAR - INSERT usando SP (cifra los datos)
                cursor.execute("""
                    EXEC Registrar_Estudiante %s, %s, %s, %s, %s, %s, %s, %s
                """, [
                    self.cleaned_data['email'],
                    self.cleaned_data['password'],
                    instance.nombre,
                    instance.apellidos,
                    instance.direccion or '',
                    instance.telefono or '',
                    instance.tipo_documento or '',
                    self.cleaned_data['numero_documento_texto']
                ])
                usuario = Usuarios.objects.get(email=self.cleaned_data['email'])
                estudiante = Estudiantes.objects.get(usuario=usuario)
                return estudiante
    
    def save_m2m(self):
        pass


class CursoForm(forms.ModelForm):
    class Meta:
        model = Cursos
        fields = ('nombre_curso', 'categoria', 'duracion_horas', 'costo', 'estado')
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        with connection.cursor() as cursor:
            if self.instance.pk:  # EDITAR - UPDATE
                cursor.execute("""
                    UPDATE Cursos 
                    SET Nombre_Curso = %s, Categoria = %s, Duracion_Horas = %s, 
                        Costo = %s, Estado = %s
                    WHERE Curso_ID = %s
                """, [
                    instance.nombre_curso, instance.categoria or '', 
                    instance.duracion_horas or 0, instance.costo, instance.estado,
                    self.instance.pk
                ])
                return instance
            else:  # CREAR - INSERT usando SP
                cursor.execute("""
                    EXEC Registrar_Curso %s, %s, %s, %s, %s
                """, [
                    instance.nombre_curso,
                    instance.categoria or '',
                    instance.duracion_horas or 0,
                    instance.costo,
                    instance.estado
                ])
                curso = Cursos.objects.get(nombre_curso=instance.nombre_curso)
                return curso
    
    def save_m2m(self):
        pass


class GrupoForm(forms.ModelForm):
    class Meta:
        model = Grupos
        fields = ('curso', 'instructor', 'cupo_maximo', 'fecha_inicio')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # EDITAR: el grupo_id no se puede modificar
            self.fields.pop('grupo_id', None)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        with connection.cursor() as cursor:
            if self.instance.pk:  # EDITAR - UPDATE
                cursor.execute("""
                    UPDATE Grupos 
                    SET Curso_ID = %s, Instructor_ID = %s, Cupo_Maximo = %s, 
                        Cupo_Disponible = %s, Fecha_Inicio = %s
                    WHERE Grupo_ID = %s
                """, [
                    instance.curso.curso_id, instance.instructor.instructor_id,
                    instance.cupo_maximo, instance.cupo_disponible, instance.fecha_inicio,
                    self.instance.pk
                ])
                return instance
            else:  # CREAR - INSERT usando SP
                cursor.execute("""
                    EXEC Registrar_Grupo %s, %s, %s, %s
                """, [
                    instance.curso.curso_id,
                    instance.instructor.instructor_id,
                    instance.cupo_maximo,
                    instance.fecha_inicio
                ])
                grupo = Grupos.objects.get(
                    curso=instance.curso,
                    instructor=instance.instructor,
                    fecha_inicio=instance.fecha_inicio
                )
                return grupo
    
    def save_m2m(self):
        pass


class InscripcionForm(forms.ModelForm):
    class Meta:
        model = Inscripciones
        fields = ('estudiante', 'grupo', 'total_pago')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Las inscripciones NO se editan (solo se crean)
            self.fields['estudiante'].disabled = True
            self.fields['grupo'].disabled = True
            self.fields['total_pago'].disabled = True
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        with connection.cursor() as cursor:
            if self.instance.pk:  # EDITAR - solo UPDATE de estado
                cursor.execute("""
                    UPDATE Inscripciones 
                    SET Estado = %s
                    WHERE Inscripcion_ID = %s
                """, [
                    instance.estado, self.instance.pk
                ])
                return instance
            else:  # CREAR - INSERT usando SP
                cursor.execute("""
                    EXEC Registrar_Inscripcion %s, %s, %s
                """, [
                    instance.estudiante.estudiante_id,
                    instance.grupo.grupo_id,
                    instance.total_pago
                ])
                inscripcion = Inscripciones.objects.get(
                    estudiante=instance.estudiante,
                    grupo=instance.grupo
                )
                return inscripcion
    
    def save_m2m(self):
        pass


class EvaluacionForm(forms.ModelForm):
    comentario_texto = forms.CharField(label='Comentarios', required=False, widget=forms.Textarea)
    
    class Meta:
        model = Evaluaciones
        fields = ('inscripcion', 'calificacion')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # EDITAR: campos que se pueden modificar
            self.fields.pop('comentario_texto', None)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        with connection.cursor() as cursor:
            if self.instance.pk:  # EDITAR - UPDATE
                cursor.execute("""
                    UPDATE Evaluaciones 
                    SET Calificacion = %s
                    WHERE Evaluacion_ID = %s
                """, [
                    instance.calificacion, self.instance.pk
                ])
                return instance
            else:  # CREAR - INSERT usando SP (cifra comentarios)
                cursor.execute("""
                    EXEC Registrar_Evaluacion %s, %s, %s
                """, [
                    instance.inscripcion.inscripcion_id,
                    instance.calificacion,
                    self.cleaned_data.get('comentario_texto', '')
                ])
                evaluacion = Evaluaciones.objects.get(inscripcion=instance.inscripcion)
                return evaluacion
    
    def save_m2m(self):
        pass


# ======================================================
# FILTROS PERSONALIZADOS
# ======================================================

class InscripcionEstadoFilter(admin.SimpleListFilter):
    title = 'Estado de inscripción'
    parameter_name = 'estado'

    def lookups(self, request, model_admin):
        return (
            ('Activa', 'Activa'),
            ('Completada', 'Completada'),
            ('Cancelada', 'Cancelada'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(estado=self.value())
        return queryset


class GrupoCupoFilter(admin.SimpleListFilter):
    title = 'Disponibilidad de cupo'
    parameter_name = 'cupo'

    def lookups(self, request, model_admin):
        return (
            ('disponible', 'Disponible'),
            ('lleno', 'Lleno'),
            ('critico', 'Crítico (<10%)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'disponible':
            return queryset.filter(cupo_disponible__gt=0)
        if self.value() == 'lleno':
            return queryset.filter(cupo_disponible=0)
        if self.value() == 'critico':
            return queryset.filter(
                cupo_disponible__gt=0,
                cupo_disponible__lte=0.1 * F('cupo_maximo')
            )
        return queryset


# ======================================================
# BASE PARA AUDITORÍAS (SOLO LECTURA)
# ======================================================

class BaseAuditoriaAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


# ======================================================
# ADMINISTRACIÓN DE ROLES Y USUARIOS
# ======================================================

@admin.register(RolesUsuario)
class RolesUsuarioAdmin(admin.ModelAdmin):
    list_display = ('rol_id', 'nombre_rol')
    ordering = ('rol_id',)


@admin.register(Usuarios)
class UsuariosAdmin(admin.ModelAdmin):
    list_display = ('usuario_id', 'email', 'rol', 'estado')
    list_filter = ('rol', 'estado')
    search_fields = ('email',)
    readonly_fields = ('contrasena',)
    
    def has_delete_permission(self, request, obj=None):
        if obj:
            tiene_estudiante = Estudiantes.objects.filter(usuario=obj).exists()
            tiene_instructor = Instructores.objects.filter(usuario=obj).exists()
            if tiene_estudiante or tiene_instructor:
                return False
        return True
    
    def delete_model(self, request, obj):
        try:
            auth_user = User.objects.filter(
                Q(username=obj.email) | Q(email=obj.email)
            ).first()
            if auth_user:
                auth_user.delete()
        except Exception:
            pass
        obj.delete()


# ======================================================
# ADMINISTRACIÓN DE ESTUDIANTES
# ======================================================

@admin.register(Estudiantes)
class EstudiantesAdmin(admin.ModelAdmin):
    form = EstudianteForm
    list_display = ('estudiante_id', 'nombre', 'apellidos', 'usuario', 'telefono', 'fecha_registro')
    search_fields = ('nombre', 'apellidos', 'usuario__email')
    list_filter = ('fecha_registro',)
    readonly_fields = ('usuario', 'fecha_registro', 'numero_documento')
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'apellidos', 'direccion', 'telefono')
        }),
        ('Datos de Identificación', {
            'fields': ('tipo_documento',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            # EDITAR: quitar campos que NO se pueden editar
            if 'email' in form.base_fields:
                del form.base_fields['email']
            if 'password' in form.base_fields:
                del form.base_fields['password']
            if 'numero_documento_texto' in form.base_fields:
                del form.base_fields['numero_documento_texto']
        return form
    
    def delete_model(self, request, obj):
        try:
            auth_user = User.objects.filter(
                Q(username=obj.usuario.email) | Q(email=obj.usuario.email)
            ).first()
            if auth_user:
                auth_user.delete()
        except Exception:
            pass
        obj.delete()
    
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            try:
                auth_user = User.objects.filter(
                    Q(username=obj.usuario.email) | Q(email=obj.usuario.email)
                ).first()
                if auth_user:
                    auth_user.delete()
            except Exception:
                pass
            obj.delete()


# ======================================================
# ADMINISTRACIÓN DE INSTRUCTORES
# ======================================================

@admin.register(Instructores)
class InstructoresAdmin(admin.ModelAdmin):
    form = InstructorForm
    list_display = ('instructor_id', 'nombre', 'apellidos', 'especialidad', 'estado', 'usuario')
    list_filter = ('estado', 'especialidad')
    search_fields = ('nombre', 'apellidos', 'usuario__email')
    readonly_fields = ('usuario', 'cedula_profesional')
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'apellidos', 'especialidad')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            # EDITAR: quitar campos que NO se pueden editar
            if 'email' in form.base_fields:
                del form.base_fields['email']
            if 'password' in form.base_fields:
                del form.base_fields['password']
            if 'cedula_profesional_texto' in form.base_fields:
                del form.base_fields['cedula_profesional_texto']
        return form
    
    def delete_model(self, request, obj):
        try:
            auth_user = User.objects.filter(
                Q(username=obj.usuario.email) | Q(email=obj.usuario.email)
            ).first()
            if auth_user:
                auth_user.delete()
        except Exception:
            pass
        obj.delete()
    
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            try:
                auth_user = User.objects.filter(
                    Q(username=obj.usuario.email) | Q(email=obj.usuario.email)
                ).first()
                if auth_user:
                    auth_user.delete()
            except Exception:
                pass
            obj.delete()


# ======================================================
# ADMINISTRACIÓN DE CURSOS
# ======================================================

@admin.register(Cursos)
class CursosAdmin(admin.ModelAdmin):
    form = CursoForm
    list_display = ('curso_id', 'nombre_curso', 'categoria', 'duracion_horas', 'costo', 'estado', 'total_inscripciones')
    list_filter = ('estado', 'categoria')
    search_fields = ('nombre_curso',)
    
    def total_inscripciones(self, obj):
        return Inscripciones.objects.filter(grupo__curso=obj).count()
    total_inscripciones.short_description = 'Inscripciones totales'


# ======================================================
# ADMINISTRACIÓN DE GRUPOS
# ======================================================

@admin.register(Grupos)
class GruposAdmin(admin.ModelAdmin):
    form = GrupoForm
    list_display = ('grupo_id', 'curso', 'instructor', 'cupo_maximo', 'cupo_disponible', 'fecha_inicio', 'ocupacion')
    list_filter = (GrupoCupoFilter, 'fecha_inicio')
    search_fields = ('grupo_id', 'curso__nombre_curso', 'instructor__nombre')
    readonly_fields = ('grupo_id',)
    
    def ocupacion(self, obj):
        if obj.cupo_maximo and obj.cupo_maximo > 0:
            try:
                cupo_max = float(obj.cupo_maximo)
                cupo_disp = float(obj.cupo_disponible)
                porcentaje = ((cupo_max - cupo_disp) / cupo_max) * 100
                
                if porcentaje >= 80:
                    color = 'red'
                elif porcentaje >= 50:
                    color = 'orange'
                else:
                    color = 'green'
                return format_html('<b style="color:{};">{:.1f}%</b>', color, porcentaje)
            except (TypeError, ValueError):
                return '-'
        return '-'
    ocupacion.short_description = 'Ocupación'


# ======================================================
# ADMINISTRACIÓN DE INSCRIPCIONES
# ======================================================

@admin.register(Inscripciones)
class InscripcionesAdmin(admin.ModelAdmin):
    form = InscripcionForm
    list_display = ('inscripcion_id', 'estudiante', 'grupo', 'fecha_inscripcion', 'estado', 'total_pago', 'promedio')
    list_filter = (InscripcionEstadoFilter, 'fecha_inscripcion')
    search_fields = ('estudiante__nombre', 'grupo__grupo_id')
    readonly_fields = ('inscripcion_id', 'fecha_inscripcion', 'total_pago')
    
    def promedio(self, obj):
        avg = obj.evaluaciones.aggregate(p=Avg('calificacion'))['p']
        if avg is not None:
            try:
                avg_float = float(avg)
                if avg_float >= 7:
                    color = 'green'
                elif avg_float >= 6:
                    color = 'orange'
                else:
                    color = 'red'
                return format_html('<span style="color:{};">{:.1f}</span>', color, avg_float)
            except (TypeError, ValueError):
                return '-'
        return '-'
    promedio.short_description = 'Promedio'


# ======================================================
# ADMINISTRACIÓN DE EVALUACIONES
# ======================================================

@admin.register(Evaluaciones)
class EvaluacionesAdmin(admin.ModelAdmin):
    form = EvaluacionForm
    list_display = ('evaluacion_id', 'inscripcion', 'calificacion', 'fecha')
    search_fields = ('inscripcion__estudiante__nombre',)
    list_filter = ('fecha',)
    readonly_fields = ('fecha', 'comentarios')
    
    fieldsets = (
        ('Información de la Evaluación', {
            'fields': ('inscripcion', 'calificacion')
        }),
    )


# ======================================================
# ADMINISTRACIÓN DE PAGOS
# ======================================================

@admin.register(Pagos)
class PagosAdmin(admin.ModelAdmin):
    list_display = ('pagos_id', 'inscripcion', 'monto', 'metodo_pago', 'fecha_pago')
    search_fields = ('inscripcion__estudiante__nombre',)
    list_filter = ('metodo_pago', 'fecha_pago')
    readonly_fields = ('pagos_id', 'referencia_pago', 'fecha_pago')
    
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DetallesPagos)
class DetallesPagosAdmin(admin.ModelAdmin):
    list_display = ('detalle_id', 'pago', 'concepto', 'cantidad', 'precio_unitario', 'subtotal')
    search_fields = ('concepto',)
    readonly_fields = ('detalle_id',)
    
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False


# ======================================================
# ADMINISTRACIÓN DE TAREAS Y ENTREGAS
# ======================================================

@admin.register(Tareas)
class TareasAdmin(admin.ModelAdmin):
    list_display = ('tarea_id', 'grupo', 'titulo', 'fecha_limite', 'puntaje_maximo', 'fecha_creacion')
    search_fields = ('titulo', 'grupo__curso__nombre_curso')
    list_filter = ('fecha_limite',)


@admin.register(Entregas)
class EntregasAdmin(admin.ModelAdmin):
    list_display = ('entrega_id', 'tarea', 'inscripcion', 'fecha_entrega', 'calificacion')
    search_fields = ('inscripcion__estudiante__nombre', 'tarea__titulo')
    list_filter = ('fecha_entrega',)


@admin.register(Mensajes)
class MensajesAdmin(admin.ModelAdmin):
    list_display = ('mensaje_id', 'emisor', 'receptor', 'asunto', 'fecha_envio', 'leido')
    search_fields = ('asunto', 'contenido', 'emisor__email', 'receptor__email')
    list_filter = ('leido', 'fecha_envio')


# ======================================================
# ADMINISTRACIÓN DE AUDITORÍAS (CON CAMPOS COMPLETOS)
# ======================================================

@admin.register(Auditoria_Inscripciones)
class AuditoriaInscripcionesAdmin(BaseAuditoriaAdmin):
    list_display = ('auditoria_ins_id', 'inscripcion_id', 'accion', 'usuario_nombre', 
                    'edo_ant', 'edo_nuevo', 'total_pago_anterior', 'total_pago_nuevo', 'fecha_evento')
    list_filter = ('accion', 'fecha_evento')
    search_fields = ('inscripcion_id', 'usuario_nombre')
    readonly_fields = [f.name for f in Auditoria_Inscripciones._meta.fields]


@admin.register(Auditoria_Evaluaciones)
class AuditoriaEvaluacionesAdmin(BaseAuditoriaAdmin):
    list_display = ('auditoria_eva_id', 'evaluacion_id', 'accion', 'usuario_nombre', 
                    'cal_ante', 'cal_nuev', 'fecha_evento')
    list_filter = ('accion', 'fecha_evento')
    search_fields = ('evaluacion_id', 'usuario_nombre')
    readonly_fields = [f.name for f in Auditoria_Evaluaciones._meta.fields]


@admin.register(Auditoria_Pagos)
class AuditoriaPagosAdmin(BaseAuditoriaAdmin):
    list_display = ('auditoria_pago_id', 'pago_id', 'accion', 'usuario_nombre', 
                    'monto_ant', 'monto_nuev', 'fecha_evento')
    list_filter = ('accion', 'fecha_evento')
    search_fields = ('pago_id', 'usuario_nombre')
    readonly_fields = [f.name for f in Auditoria_Pagos._meta.fields]


@admin.register(Auditoria_Estudiantes)
class AuditoriaEstudiantesAdmin(BaseAuditoriaAdmin):
    list_display = ('auditoria_est_id', 'estudiante_id', 'accion', 'usuario_nombre',
                    'nombre_ant', 'nombre_nuev', 'apellidos_ant', 'apellidos_nuev',
                    'telefono_ant', 'telefono_nuev', 'direccion_ant', 'direccion_nuev',
                    'tipo_documento_ant', 'tipo_documento_nuev', 'fecha_evento')
    list_filter = ('accion', 'fecha_evento')
    search_fields = ('estudiante_id', 'usuario_nombre', 'nombre_ant', 'nombre_nuev')
    readonly_fields = [f.name for f in Auditoria_Estudiantes._meta.fields]


@admin.register(Auditoria_Entregas)
class AuditoriaEntregasAdmin(BaseAuditoriaAdmin):
    list_display = ('auditoria_ent_id', 'entrega_id', 'accion', 'usuario_nombre',
                    'comentario_ant', 'comentario_nuev', 'calificacion_ant', 'calificacion_nuev', 'fecha_evento')
    list_filter = ('accion', 'fecha_evento')
    search_fields = ('entrega_id', 'usuario_nombre')
    readonly_fields = [f.name for f in Auditoria_Entregas._meta.fields]


@admin.register(Auditoria_Instructores)
class AuditoriaInstructoresAdmin(BaseAuditoriaAdmin):
    list_display = ('auditoria_ins_id', 'instructor_id', 'accion', 'usuario_nombre',
                    'nombre_ant', 'nombre_nuev', 'apellidos_ant', 'apellidos_nuev',
                    'especialidad_ant', 'especialidad_nuev', 'estado_ant', 'estado_nuev', 'fecha_evento')
    list_filter = ('accion', 'fecha_evento')
    search_fields = ('instructor_id', 'usuario_nombre')
    readonly_fields = [f.name for f in Auditoria_Instructores._meta.fields]


@admin.register(Auditoria_Cursos)
class AuditoriaCursosAdmin(BaseAuditoriaAdmin):
    list_display = ('auditoria_cur_id', 'curso_id', 'accion', 'usuario_nombre',
                    'nombre_ant', 'nombre_nuev', 'categoria_ant', 'categoria_nuev',
                    'duracion_ant', 'duracion_nuev', 'costo_ant', 'costo_nuev',
                    'estado_ant', 'estado_nuev', 'fecha_evento')
    list_filter = ('accion', 'fecha_evento')
    search_fields = ('curso_id', 'usuario_nombre')
    readonly_fields = [f.name for f in Auditoria_Cursos._meta.fields]


@admin.register(Auditoria_Grupos)
class AuditoriaGruposAdmin(BaseAuditoriaAdmin):
    list_display = ('auditoria_gru_id', 'grupo_id', 'accion', 'usuario_nombre',
                    'curso_ant', 'curso_nuev', 'instructor_ant', 'instructor_nuev',
                    'cupo_maximo_ant', 'cupo_maximo_nuev', 'cupo_disponible_ant', 'cupo_disponible_nuev',
                    'fecha_inicio_ant', 'fecha_inicio_nuev', 'fecha_evento')
    list_filter = ('accion', 'fecha_evento')
    search_fields = ('grupo_id', 'usuario_nombre')
    readonly_fields = [f.name for f in Auditoria_Grupos._meta.fields]


# ======================================================
# MODELOS FRAGMENTADOS VERTICALES (SOLO REGISTRO)
# ======================================================

admin.site.register(Estudiantes_Normales)
admin.site.register(Estudiantes_Sensibles)
admin.site.register(Instructores_Normales)
admin.site.register(Instructores_Cedulas)


# ======================================================
# PERSONALIZACIÓN DEL SITIO DE ADMIN
# ======================================================

admin.site.site_header = 'Sistema de Educación Online'
admin.site.site_title = 'Portal de Administración'
admin.site.index_title = 'Bienvenido al Panel de Control'