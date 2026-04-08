from django.db import models

# ============================================
# MODELOS PRINCIPALES
# ============================================

class RolesUsuario(models.Model):
    rol_id = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50)

    class Meta:
        db_table = 'Roles_Usuario'
        managed = False

    def __str__(self):
        return self.nombre_rol


class Usuarios(models.Model):
    usuario_id = models.AutoField(primary_key=True)
    rol = models.ForeignKey(RolesUsuario, on_delete=models.CASCADE, db_column='Rol_ID')
    email = models.CharField(max_length=100, unique=True)
    contrasena = models.BinaryField()
    estado = models.CharField(max_length=20)

    class Meta:
        db_table = 'Usuarios'
        managed = False

    def __str__(self):
        return self.email


class Estudiantes(models.Model):
    estudiante_id = models.AutoField(primary_key=True)
    usuario = models.OneToOneField(Usuarios, on_delete=models.CASCADE, db_column='Usuario_ID')
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    direccion = models.CharField(max_length=150, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    tipo_documento = models.CharField(max_length=20, null=True, blank=True)
    numero_documento = models.BinaryField()
    fecha_registro = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'Estudiantes'
        managed = False

    def __str__(self):
        return f"{self.nombre} {self.apellidos}"


class Instructores(models.Model):
    instructor_id = models.AutoField(primary_key=True)
    usuario = models.OneToOneField(Usuarios, on_delete=models.CASCADE, db_column='Usuario_ID')
    nombre = models.CharField(max_length=50)
    apellidos = models.CharField(max_length=50)
    especialidad = models.CharField(max_length=50, null=True, blank=True)
    cedula_profesional = models.BinaryField()
    estado = models.CharField(max_length=20)

    class Meta:
        db_table = 'Instructores'
        managed = False

    def __str__(self):
        return f"{self.nombre} {self.apellidos} - {self.especialidad}"


class Cursos(models.Model):
    curso_id = models.AutoField(primary_key=True)
    nombre_curso = models.CharField(max_length=100)
    categoria = models.CharField(max_length=50, null=True, blank=True)
    duracion_horas = models.IntegerField(null=True, blank=True)
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20)

    class Meta:
        db_table = 'Cursos'
        managed = False

    def __str__(self):
        return f"{self.nombre_curso} - ${self.costo}"


class Grupos(models.Model):
    grupo_id = models.CharField(primary_key=True, max_length=20, db_column='Grupo_ID')
    curso = models.ForeignKey(Cursos, on_delete=models.CASCADE, db_column='Curso_ID', related_name='grupos')
    instructor = models.ForeignKey(Instructores, on_delete=models.CASCADE, db_column='Instructor_ID')
    cupo_maximo = models.IntegerField()
    cupo_disponible = models.IntegerField()
    fecha_inicio = models.DateField()

    class Meta:
        db_table = 'Grupos'
        managed = False

    def __str__(self):
        return f"{self.grupo_id} - {self.curso.nombre_curso}"


class Inscripciones(models.Model):
    inscripcion_id = models.IntegerField(primary_key=True)
    estudiante = models.ForeignKey(Estudiantes, on_delete=models.CASCADE, db_column='Estudiante_ID', related_name='inscripciones')
    grupo = models.ForeignKey(Grupos, on_delete=models.CASCADE, db_column='Grupo_ID', related_name='inscripciones')
    fecha_inscripcion = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=20)
    total_pago = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'Inscripciones'
        managed = False

    def __str__(self):
        return f"Inscripción {self.inscripcion_id} - {self.estudiante}"


class Evaluaciones(models.Model):
    evaluacion_id = models.AutoField(primary_key=True)
    inscripcion = models.ForeignKey(Inscripciones, on_delete=models.CASCADE, db_column='Inscripcion_ID', related_name='evaluaciones')
    calificacion = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    comentarios = models.BinaryField(null=True, blank=True)
    fecha = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'Evaluaciones'
        managed = False

    def __str__(self):
        return f"Evaluación {self.evaluacion_id} - {self.calificacion}"


class Pagos(models.Model):
    pagos_id = models.AutoField(primary_key=True)
    inscripcion = models.ForeignKey(Inscripciones, on_delete=models.CASCADE, db_column='Inscripcion_ID', related_name='pagos')
    metodo_pago = models.CharField(max_length=30)
    fecha_pago = models.DateField(auto_now_add=True)
    referencia_pago = models.BinaryField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'Pagos'
        managed = False

    def __str__(self):
        return f"Pago {self.pagos_id} - ${self.monto}"


class DetallesPagos(models.Model):
    detalle_id = models.AutoField(primary_key=True)
    pago = models.ForeignKey(Pagos, on_delete=models.CASCADE, db_column='Pago_ID', related_name='detalles')
    concepto = models.CharField(max_length=100)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'DetallesPagos'
        managed = False


# ============================================
# MODELOS DE AUDITORÍA
# ============================================

class Auditoria_Inscripciones(models.Model):
    auditoria_ins_id = models.AutoField(primary_key=True, db_column='Auditoria_Ins_ID')
    inscripcion_id = models.IntegerField(db_column='Inscripcion_ID')
    accion = models.CharField(max_length=10, db_column='Accion')
    usuario_id = models.IntegerField(null=True, blank=True, db_column='usuario_id')
    usuario_nombre = models.CharField(max_length=100, null=True, blank=True, db_column='usuario_nombre')
    edo_ant = models.CharField(max_length=20, null=True, blank=True, db_column='edo_ant')
    edo_nuevo = models.CharField(max_length=20, null=True, blank=True, db_column='edo_nuevo')
    total_pago_anterior = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_column='total_pago_anterior')
    total_pago_nuevo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_column='total_pago_nuevo')
    fecha_evento = models.DateTimeField(auto_now_add=True, db_column='Fecha_Evento')

    class Meta:
        db_table = 'Auditoria_Inscripciones'
        managed = False
        ordering = ['-fecha_evento']

    def __str__(self):
        return f"Auditoría {self.auditoria_ins_id} - {self.accion}"


class Auditoria_Evaluaciones(models.Model):
    auditoria_eva_id = models.AutoField(primary_key=True, db_column='Auditoria_Eva_ID')
    evaluacion_id = models.IntegerField(db_column='Evaluacion_ID')
    accion = models.CharField(max_length=10, db_column='Accion')
    usuario_id = models.IntegerField(null=True, blank=True, db_column='usuario_id')
    usuario_nombre = models.CharField(max_length=100, null=True, blank=True, db_column='usuario_nombre')
    cal_ante = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, db_column='cal_ante')
    cal_nuev = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, db_column='cal_nuev')
    coment_ant = models.BinaryField(null=True, blank=True, db_column='coment_ant')
    coment_nuev = models.BinaryField(null=True, blank=True, db_column='coment_nuev')
    fecha_evento = models.DateTimeField(auto_now_add=True, db_column='Fecha_Evento')

    class Meta:
        db_table = 'Auditoria_Evaluaciones'
        managed = False
        ordering = ['-fecha_evento']

    def __str__(self):
        return f"Auditoría {self.auditoria_eva_id} - {self.accion}"


class Auditoria_Pagos(models.Model):
    auditoria_pago_id = models.AutoField(primary_key=True, db_column='Auditoria_Pago_ID')
    pago_id = models.IntegerField(db_column='Pago_ID')
    accion = models.CharField(max_length=10, db_column='Accion')
    usuario_id = models.IntegerField(null=True, blank=True, db_column='usuario_id')
    usuario_nombre = models.CharField(max_length=100, null=True, blank=True, db_column='usuario_nombre')
    monto_ant = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_column='Monto_ant')
    monto_nuev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_column='Monto_nuev')
    referencia_pago_ant = models.BinaryField(null=True, blank=True, db_column='Referencia_pago_ant')
    referencia_pago_nuev = models.BinaryField(null=True, blank=True, db_column='Referencia_pago_nuev')
    fecha_evento = models.DateTimeField(auto_now_add=True, db_column='Fecha_Evento')

    class Meta:
        db_table = 'Auditoria_Pagos'
        managed = False
        ordering = ['-fecha_evento']

    def __str__(self):
        return f"Auditoría {self.auditoria_pago_id} - {self.accion}"


class Auditoria_Estudiantes(models.Model):
    auditoria_est_id = models.AutoField(primary_key=True, db_column='Auditoria_Est_ID')
    estudiante_id = models.IntegerField(db_column='Estudiante_ID')
    accion = models.CharField(max_length=10, db_column='Accion')
    usuario_id = models.IntegerField(null=True, blank=True, db_column='usuario_id')
    usuario_nombre = models.CharField(max_length=100, null=True, blank=True, db_column='usuario_nombre')
    nombre_ant = models.CharField(max_length=100, null=True, blank=True, db_column='Nombre_Ant')
    nombre_nuev = models.CharField(max_length=100, null=True, blank=True, db_column='Nombre_Nuev')
    apellidos_ant = models.CharField(max_length=100, null=True, blank=True, db_column='Apellidos_Ant')
    apellidos_nuev = models.CharField(max_length=100, null=True, blank=True, db_column='Apellidos_Nuev')
    telefono_ant = models.CharField(max_length=20, null=True, blank=True, db_column='Telefono_Ant')
    telefono_nuev = models.CharField(max_length=20, null=True, blank=True, db_column='Telefono_Nuev')
    direccion_ant = models.CharField(max_length=150, null=True, blank=True, db_column='Direccion_Ant')
    direccion_nuev = models.CharField(max_length=150, null=True, blank=True, db_column='Direccion_Nuev')
    tipo_documento_ant = models.CharField(max_length=20, null=True, blank=True, db_column='Tipo_Documento_Ant')
    tipo_documento_nuev = models.CharField(max_length=20, null=True, blank=True, db_column='Tipo_Documento_Nuev')
    numero_documento_ant = models.BinaryField(null=True, blank=True, db_column='Numero_Documento_Ant')
    numero_documento_nuev = models.BinaryField(null=True, blank=True, db_column='Numero_Documento_Nuev')
    fecha_evento = models.DateTimeField(auto_now_add=True, db_column='Fecha_Evento')

    class Meta:
        db_table = 'Auditoria_Estudiantes'
        managed = False
        ordering = ['-fecha_evento']

    def __str__(self):
        return f"Auditoría {self.auditoria_est_id} - {self.accion}"


class Auditoria_Entregas(models.Model):
    auditoria_ent_id = models.AutoField(primary_key=True, db_column='Auditoria_Ent_ID')
    entrega_id = models.IntegerField(db_column='Entrega_ID')
    accion = models.CharField(max_length=10, db_column='Accion')
    usuario_id = models.IntegerField(null=True, blank=True, db_column='usuario_id')
    usuario_nombre = models.CharField(max_length=100, null=True, blank=True, db_column='usuario_nombre')
    archivo_ant = models.BinaryField(null=True, blank=True, db_column='Archivo_Ant')
    archivo_nuev = models.BinaryField(null=True, blank=True, db_column='Archivo_Nuev')
    comentario_ant = models.CharField(max_length=500, null=True, blank=True, db_column='Comentario_Ant')
    comentario_nuev = models.CharField(max_length=500, null=True, blank=True, db_column='Comentario_Nuev')
    calificacion_ant = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, db_column='Calificacion_Ant')
    calificacion_nuev = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, db_column='Calificacion_Nuev')
    fecha_evento = models.DateTimeField(auto_now_add=True, db_column='Fecha_Evento')

    class Meta:
        db_table = 'Auditoria_Entregas'
        managed = False
        ordering = ['-fecha_evento']

    def __str__(self):
        return f"Auditoría {self.auditoria_ent_id} - {self.accion}"


class Auditoria_Instructores(models.Model):
    auditoria_ins_id = models.AutoField(primary_key=True, db_column='Auditoria_Ins_Inst_ID')
    instructor_id = models.IntegerField(db_column='Instructor_ID')
    accion = models.CharField(max_length=10, db_column='Accion')
    usuario_id = models.IntegerField(null=True, blank=True, db_column='usuario_id')
    usuario_nombre = models.CharField(max_length=100, null=True, blank=True, db_column='usuario_nombre')
    nombre_ant = models.CharField(max_length=50, null=True, blank=True, db_column='Nombre_Ant')
    nombre_nuev = models.CharField(max_length=50, null=True, blank=True, db_column='Nombre_Nuev')
    apellidos_ant = models.CharField(max_length=50, null=True, blank=True, db_column='Apellidos_Ant')
    apellidos_nuev = models.CharField(max_length=50, null=True, blank=True, db_column='Apellidos_Nuev')
    especialidad_ant = models.CharField(max_length=50, null=True, blank=True, db_column='Especialidad_Ant')
    especialidad_nuev = models.CharField(max_length=50, null=True, blank=True, db_column='Especialidad_Nuev')
    estado_ant = models.CharField(max_length=20, null=True, blank=True, db_column='Estado_Ant')
    estado_nuev = models.CharField(max_length=20, null=True, blank=True, db_column='Estado_Nuev')
    cedula_ant = models.BinaryField(null=True, blank=True, db_column='Cedula_Ant')
    cedula_nuev = models.BinaryField(null=True, blank=True, db_column='Cedula_Nuev')
    fecha_evento = models.DateTimeField(auto_now_add=True, db_column='Fecha_Evento')

    class Meta:
        db_table = 'Auditoria_Instructores'
        managed = False
        ordering = ['-fecha_evento']

    def __str__(self):
        return f"Auditoría {self.auditoria_ins_id} - {self.accion}"


class Auditoria_Cursos(models.Model):
    auditoria_cur_id = models.AutoField(primary_key=True, db_column='Auditoria_Cur_ID')
    curso_id = models.IntegerField(db_column='Curso_ID')
    accion = models.CharField(max_length=10, db_column='Accion')
    usuario_id = models.IntegerField(null=True, blank=True, db_column='usuario_id')
    usuario_nombre = models.CharField(max_length=100, null=True, blank=True, db_column='usuario_nombre')
    nombre_ant = models.CharField(max_length=100, null=True, blank=True, db_column='Nombre_Ant')
    nombre_nuev = models.CharField(max_length=100, null=True, blank=True, db_column='Nombre_Nuev')
    categoria_ant = models.CharField(max_length=50, null=True, blank=True, db_column='Categoria_Ant')
    categoria_nuev = models.CharField(max_length=50, null=True, blank=True, db_column='Categoria_Nuev')
    duracion_ant = models.IntegerField(null=True, blank=True, db_column='Duracion_Ant')
    duracion_nuev = models.IntegerField(null=True, blank=True, db_column='Duracion_Nuev')
    costo_ant = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_column='Costo_Ant')
    costo_nuev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_column='Costo_Nuev')
    estado_ant = models.CharField(max_length=20, null=True, blank=True, db_column='Estado_Ant')
    estado_nuev = models.CharField(max_length=20, null=True, blank=True, db_column='Estado_Nuev')
    fecha_evento = models.DateTimeField(auto_now_add=True, db_column='Fecha_Evento')

    class Meta:
        db_table = 'Auditoria_Cursos'
        managed = False
        ordering = ['-fecha_evento']

    def __str__(self):
        return f"Auditoría {self.auditoria_cur_id} - {self.accion}"


class Auditoria_Grupos(models.Model):
    auditoria_gru_id = models.AutoField(primary_key=True, db_column='Auditoria_Gru_ID')
    grupo_id = models.CharField(max_length=20, db_column='Grupo_ID')
    accion = models.CharField(max_length=10, db_column='Accion')
    usuario_id = models.IntegerField(null=True, blank=True, db_column='usuario_id')
    usuario_nombre = models.CharField(max_length=100, null=True, blank=True, db_column='usuario_nombre')
    curso_ant = models.IntegerField(null=True, blank=True, db_column='Curso_Ant')
    curso_nuev = models.IntegerField(null=True, blank=True, db_column='Curso_Nuev')
    instructor_ant = models.IntegerField(null=True, blank=True, db_column='Instructor_Ant')
    instructor_nuev = models.IntegerField(null=True, blank=True, db_column='Instructor_Nuev')
    cupo_maximo_ant = models.IntegerField(null=True, blank=True, db_column='Cupo_Maximo_Ant')
    cupo_maximo_nuev = models.IntegerField(null=True, blank=True, db_column='Cupo_Maximo_Nuev')
    cupo_disponible_ant = models.IntegerField(null=True, blank=True, db_column='Cupo_Disponible_Ant')
    cupo_disponible_nuev = models.IntegerField(null=True, blank=True, db_column='Cupo_Disponible_Nuev')
    fecha_inicio_ant = models.DateField(null=True, blank=True, db_column='Fecha_Inicio_Ant')
    fecha_inicio_nuev = models.DateField(null=True, blank=True, db_column='Fecha_Inicio_Nuev')
    fecha_evento = models.DateTimeField(auto_now_add=True, db_column='Fecha_Evento')

    class Meta:
        db_table = 'Auditoria_Grupos'
        managed = False
        ordering = ['-fecha_evento']

    def __str__(self):
        return f"Auditoría {self.auditoria_gru_id} - {self.accion}"


# ============================================
# MODELOS DE TAREAS, ENTREGAS Y MENSAJES
# ============================================

class Tareas(models.Model):
    tarea_id = models.AutoField(primary_key=True)
    grupo = models.ForeignKey(Grupos, on_delete=models.CASCADE, db_column='Grupo_ID', related_name='tareas')
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField(null=True, blank=True)
    fecha_limite = models.DateField()
    puntaje_maximo = models.DecimalField(max_digits=5, decimal_places=2)
    creado_por = models.ForeignKey(Usuarios, on_delete=models.CASCADE, db_column='Creado_Por', related_name='tareas_creadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Tareas'
        managed = False

    def __str__(self):
        return f"{self.titulo} - {self.grupo.grupo_id}"


class Entregas(models.Model):
    entrega_id = models.AutoField(primary_key=True)
    tarea = models.ForeignKey(Tareas, on_delete=models.CASCADE, db_column='Tarea_ID', related_name='entregas')
    inscripcion = models.ForeignKey(Inscripciones, on_delete=models.CASCADE, db_column='Inscripcion_ID', related_name='entregas')
    archivo = models.BinaryField(null=True, blank=True)
    comentario = models.CharField(max_length=500, null=True, blank=True)
    fecha_entrega = models.DateTimeField(auto_now_add=True)
    calificacion = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    comentario_instructor = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = 'Entregas'
        managed = False

    def __str__(self):
        return f"Entrega {self.entrega_id} - Tarea {self.tarea.tarea_id}"


class Mensajes(models.Model):
    mensaje_id = models.AutoField(primary_key=True)
    emisor = models.ForeignKey(Usuarios, on_delete=models.CASCADE, db_column='Emisor_ID', related_name='mensajes_enviados')
    receptor = models.ForeignKey(Usuarios, on_delete=models.CASCADE, db_column='Receptor_ID', related_name='mensajes_recibidos')
    asunto = models.CharField(max_length=100, null=True, blank=True)
    contenido = models.CharField(max_length=4000, db_column='Contenido')
    fecha_envio = models.DateTimeField(auto_now_add=True, db_column='Fecha_Envio')
    leido = models.BooleanField(default=False, db_column='Leido')
    tarea = models.ForeignKey(Tareas, on_delete=models.CASCADE, db_column='Tarea_ID', null=True, blank=True, related_name='mensajes')

    class Meta:
        db_table = 'Mensajes'
        managed = False

    def __str__(self):
        return f"Mensaje {self.mensaje_id} - {self.emisor.email} -> {self.receptor.email}"