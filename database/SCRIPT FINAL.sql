
-- 1. BORRAR BASE DE DATOS SI EXISTE
USE master;
GO

IF EXISTS (SELECT name FROM sys.databases WHERE name = 'Online_Education')
BEGIN
    ALTER DATABASE Online_Education SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE Online_Education;
END
GO


-- 2. CREAR BASE DE DATOS

CREATE DATABASE Online_Education;
GO
USE Online_Education;
GO

-- 3. CREAR TABLAS PRINCIPALES


CREATE TABLE Roles_Usuario(
    Rol_ID INT IDENTITY(1,1) PRIMARY KEY,
    Nombre_Rol VARCHAR(50) NOT NULL                 
);
GO

CREATE TABLE Usuarios(
    Usuario_ID INT IDENTITY(1,1) PRIMARY KEY,
    Rol_ID INT NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    Contrasena VARBINARY(MAX) NOT NULL,
    Estado VARCHAR(20) NOT NULL,
    CONSTRAINT FK_Usuarios_Roles FOREIGN KEY (Rol_ID) REFERENCES Roles_Usuario(Rol_ID),
    CONSTRAINT CHK_Usuario_Estado CHECK (Estado IN ('Activo', 'Inactivo', 'Suspendido'))
);
GO

CREATE TABLE Estudiantes (
    Estudiante_ID INT IDENTITY(1,1) PRIMARY KEY,
    Usuario_ID INT NOT NULL UNIQUE, 
    Nombre VARCHAR(100) NOT NULL,
    Apellidos VARCHAR(100) NOT NULL,
    Direccion VARCHAR(150),
    Telefono VARCHAR(20),
    Tipo_Documento VARCHAR(20),
    Numero_Documento VARBINARY(MAX) NOT NULL,
    Fecha_Registro DATE DEFAULT GETDATE(),
    CONSTRAINT FK_Estudiantes_Usuarios FOREIGN KEY (Usuario_ID) REFERENCES Usuarios(Usuario_ID)
);
GO

CREATE TABLE Instructores(
    Instructor_ID INT IDENTITY(1,1) PRIMARY KEY,
    Usuario_ID INT NOT NULL UNIQUE,
    Nombre VARCHAR(50) NOT NULL,
    Apellidos VARCHAR(50) NOT NULL,
    Especialidad VARCHAR(50),
    Cedula_Profesional VARBINARY(MAX) NOT NULL,
    Estado VARCHAR(20) NOT NULL,
    CONSTRAINT FK_Instructores_Usuarios FOREIGN KEY (Usuario_ID) REFERENCES Usuarios(Usuario_ID),
    CONSTRAINT CHK_Instructor_Estado CHECK (Estado IN ('Activo', 'Inactivo', 'Suspendido'))
);
GO

CREATE TABLE Cursos(
    Curso_ID INT IDENTITY(1,1) PRIMARY KEY,
    Nombre_Curso VARCHAR(100) NOT NULL,
    Categoria VARCHAR(50),
    Duracion_Horas INT,
    Costo DECIMAL(10,2) NOT NULL,
    Estado VARCHAR(20) NOT NULL,
    CONSTRAINT CHK_Curso_Estado CHECK (Estado IN ('Activo', 'Inactivo', 'Lleno', 'Completado'))
);
GO

-- 4. SECUENCIAS


CREATE SEQUENCE Seq_Grupo
    START WITH 1
    INCREMENT BY 1;
GO

CREATE SEQUENCE Folio_Inscription
    START WITH 1000
    INCREMENT BY 1;
GO


-- 5. TABLA GRUPOS


CREATE TABLE Grupos(
    Grupo_ID VARCHAR(20) PRIMARY KEY 
        DEFAULT CONCAT('GRUPO-', FORMAT(NEXT VALUE FOR Seq_Grupo, '0000')),
    Curso_ID INT NOT NULL,
    Instructor_ID INT NOT NULL,
    Cupo_Maximo INT NOT NULL,
    Cupo_Disponible INT NOT NULL,
    Fecha_Inicio DATE NOT NULL,
    CONSTRAINT FK_Grupos_Cursos FOREIGN KEY (Curso_ID) REFERENCES Cursos(Curso_ID),
    CONSTRAINT FK_Grupos_Instructores FOREIGN KEY (Instructor_ID) REFERENCES Instructores(Instructor_ID),
    CONSTRAINT CHK_Cupo CHECK (Cupo_Disponible >= 0 AND Cupo_Disponible <= Cupo_Maximo)
);
GO

-- 6. TABLA INSCRIPCIONES


CREATE TABLE Inscripciones(
    Inscripcion_ID INT IDENTITY(1000,1) PRIMARY KEY,
    Estudiante_ID INT NOT NULL,
    Grupo_ID VARCHAR(20) NOT NULL,
    Fecha_Inscripcion DATE DEFAULT GETDATE(),
    Estado VARCHAR(20) NOT NULL,
    Total_Pago DECIMAL(10,2) NOT NULL,
    CONSTRAINT FK_Inscripciones_Estudiantes FOREIGN KEY (Estudiante_ID) REFERENCES Estudiantes(Estudiante_ID),
    CONSTRAINT FK_Inscripciones_Grupos FOREIGN KEY (Grupo_ID) REFERENCES Grupos(Grupo_ID),
    CONSTRAINT CHK_Inscripcion_Estado CHECK (Estado IN ('Activa', 'Completada', 'Cancelada'))
);
GO

-- 7. RESTO DE TABLAS


CREATE TABLE Evaluaciones(
    Evaluacion_ID INT IDENTITY(1,1) PRIMARY KEY,
    Inscripcion_ID INT NOT NULL,
    Calificacion DECIMAL(5,2),
    Comentarios VARBINARY(MAX),
    Fecha DATE DEFAULT GETDATE(),
    CONSTRAINT FK_Evaluaciones_Inscripciones FOREIGN KEY (Inscripcion_ID) REFERENCES Inscripciones(Inscripcion_ID),
    CONSTRAINT CHK_Calificacion CHECK (Calificacion >= 0 AND Calificacion <= 10)
);
GO

CREATE TABLE Pagos(
    Pagos_ID INT IDENTITY(1,1) PRIMARY KEY,
    Inscripcion_ID INT NOT NULL,
    Metodo_Pago VARCHAR(30) NOT NULL,
    Fecha_Pago DATE DEFAULT GETDATE(),
    Referencia_Pago VARBINARY(MAX) NOT NULL,
    Monto DECIMAL(10,2) NOT NULL,
    CONSTRAINT FK_Pagos_Inscripciones FOREIGN KEY (Inscripcion_ID) REFERENCES Inscripciones(Inscripcion_ID),
    CONSTRAINT CHK_Monto_Positivo CHECK (Monto > 0)
);
GO

CREATE TABLE DetallesPagos(
    Detalle_ID INT IDENTITY(1,1) PRIMARY KEY,
    Pago_ID INT NOT NULL,
    Concepto VARCHAR(100) NOT NULL,
    Cantidad INT NOT NULL,
    Precio_Unitario DECIMAL(10,2) NOT NULL,
    Subtotal DECIMAL(10,2) NOT NULL,
    CONSTRAINT FK_Detalles_Pagos FOREIGN KEY (Pago_ID) REFERENCES Pagos(Pagos_ID),
    CONSTRAINT CHK_Cantidad_Positiva CHECK (Cantidad > 0)
);
GO

CREATE TABLE Tareas(
    Tarea_ID INT IDENTITY(1,1) PRIMARY KEY,
    Grupo_ID VARCHAR(20) NOT NULL,
    Titulo VARCHAR(100) NOT NULL,
    Descripcion TEXT,
    Fecha_Limite DATE NOT NULL,
    Puntaje_Maximo DECIMAL(5,2) NOT NULL,
    Creado_Por INT NOT NULL,
    Fecha_Creacion DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_Tareas_Grupos FOREIGN KEY (Grupo_ID) REFERENCES Grupos(Grupo_ID),
    CONSTRAINT FK_Tareas_Usuarios FOREIGN KEY (Creado_Por) REFERENCES Usuarios(Usuario_ID),
    CONSTRAINT CHK_Puntaje_Maximo CHECK (Puntaje_Maximo > 0)
);
GO

CREATE TABLE Entregas(
    Entrega_ID INT IDENTITY(1,1) PRIMARY KEY,
    Tarea_ID INT NOT NULL,
    Inscripcion_ID INT NOT NULL,
    Archivo VARBINARY(MAX),
    Comentario VARCHAR(500),
    Fecha_Entrega DATETIME DEFAULT GETDATE(),
    Calificacion DECIMAL(5,2),
    Comentario_Instructor VARCHAR(500),
    CONSTRAINT FK_Entregas_Tareas FOREIGN KEY (Tarea_ID) REFERENCES Tareas(Tarea_ID),
    CONSTRAINT FK_Entregas_Inscripciones FOREIGN KEY (Inscripcion_ID) REFERENCES Inscripciones(Inscripcion_ID),
    CONSTRAINT CHK_Entrega_Calificacion CHECK (Calificacion >= 0 AND Calificacion <= 10)
);
GO

CREATE TABLE Mensajes(
    Mensaje_ID INT IDENTITY(1,1) PRIMARY KEY,
    Emisor_ID INT NOT NULL,
    Receptor_ID INT NOT NULL,
    Asunto VARCHAR(100),
    Contenido TEXT NOT NULL,
    Fecha_Envio DATETIME DEFAULT GETDATE(),
    Leido BIT DEFAULT 0,
    Tarea_ID INT NULL,
    CONSTRAINT FK_Mensajes_Emisor FOREIGN KEY (Emisor_ID) REFERENCES Usuarios(Usuario_ID),
    CONSTRAINT FK_Mensajes_Receptor FOREIGN KEY (Receptor_ID) REFERENCES Usuarios(Usuario_ID),
    CONSTRAINT FK_Mensajes_Tareas FOREIGN KEY (Tarea_ID) REFERENCES Tareas(Tarea_ID)
);
GO


-- 8. TABLAS DE AUDITORIA


CREATE TABLE Bitacora_Errores(
    Error_Log_ID INT IDENTITY(1,1) PRIMARY KEY,
    Usuario_DB VARCHAR(50) DEFAULT SUSER_SNAME(),      
    Numero_Error INT,
    Mensaje_Error VARCHAR(MAX),
    Procedimiento VARCHAR(100),
    Linea_Error INT,
    Fecha_Hora DATETIME DEFAULT GETDATE()
);
GO

CREATE TABLE Auditoria_Inscripciones(
    Auditoria_Ins_ID INT IDENTITY(1,1) PRIMARY KEY,
    Inscripcion_ID INT NOT NULL,
    Accion VARCHAR(10) NOT NULL,
    usuario_id INT NULL,
    usuario_nombre VARCHAR(100) NULL,
    edo_ant VARCHAR(20),
    edo_nuevo VARCHAR(20),
    total_pago_anterior DECIMAL(10,2),
    total_pago_nuevo DECIMAL(10,2),
    Fecha_Evento DATETIME DEFAULT GETDATE()
);
GO

CREATE TABLE Auditoria_Evaluaciones(
    Auditoria_Eva_ID INT IDENTITY(1,1) PRIMARY KEY,
    Evaluacion_ID INT NOT NULL,
    Accion VARCHAR(10) NOT NULL,
    usuario_id INT NULL,
    usuario_nombre VARCHAR(100) NULL,
    cal_ante DECIMAL(5,2),
    cal_nuev DECIMAL(5,2),
    coment_ant VARBINARY(MAX), 
    coment_nuev VARBINARY(MAX), 
    Fecha_Evento DATETIME DEFAULT GETDATE()
);
GO

CREATE TABLE Auditoria_Pagos(
    Auditoria_Pago_ID INT IDENTITY(1,1) PRIMARY KEY,
    Pago_ID INT NOT NULL,
    Accion VARCHAR(10) NOT NULL,
    usuario_id INT NULL,
    usuario_nombre VARCHAR(100) NULL,
    Monto_ant DECIMAL(10,2),
    Monto_nuev DECIMAL(10,2),
    Referencia_pago_ant VARBINARY(MAX), 
    Referencia_pago_nuev VARBINARY(MAX), 
    Fecha_Evento DATETIME DEFAULT GETDATE()
);
GO

CREATE TABLE Auditoria_Estudiantes(
    Auditoria_Est_ID INT IDENTITY(1,1) PRIMARY KEY,
    Estudiante_ID INT NOT NULL,
    Accion VARCHAR(10) NOT NULL,
    usuario_id INT NULL,
    usuario_nombre VARCHAR(100) NULL,
    Nombre_Ant VARCHAR(100),
    Nombre_Nuev VARCHAR(100),
    Apellidos_Ant VARCHAR(100),
    Apellidos_Nuev VARCHAR(100),
    Telefono_Ant VARCHAR(20),
    Telefono_Nuev VARCHAR(20),
    Direccion_Ant VARCHAR(150),
    Direccion_Nuev VARCHAR(150),
    Tipo_Documento_Ant VARCHAR(20),
    Tipo_Documento_Nuev VARCHAR(20),
    Numero_Documento_Ant VARBINARY(MAX),
    Numero_Documento_Nuev VARBINARY(MAX),
    Fecha_Evento DATETIME DEFAULT GETDATE()
);
GO

CREATE TABLE Auditoria_Entregas(
    Auditoria_Ent_ID INT IDENTITY(1,1) PRIMARY KEY,
    Entrega_ID INT NOT NULL,
    Accion VARCHAR(10) NOT NULL,
    usuario_id INT NULL,
    usuario_nombre VARCHAR(100) NULL,
    Archivo_Ant VARBINARY(MAX),
    Archivo_Nuev VARBINARY(MAX),
    Comentario_Ant VARCHAR(500),
    Comentario_Nuev VARCHAR(500),
    Calificacion_Ant DECIMAL(5,2),
    Calificacion_Nuev DECIMAL(5,2),
    Fecha_Evento DATETIME DEFAULT GETDATE()
);
GO

CREATE TABLE Auditoria_Instructores(
    Auditoria_Ins_Inst_ID INT IDENTITY(1,1) PRIMARY KEY,
    Instructor_ID INT NOT NULL,
    Accion VARCHAR(10) NOT NULL,
    usuario_id INT NULL,
    usuario_nombre VARCHAR(100) NULL,
    Nombre_Ant VARCHAR(50),
    Nombre_Nuev VARCHAR(50),
    Apellidos_Ant VARCHAR(50),
    Apellidos_Nuev VARCHAR(50),
    Especialidad_Ant VARCHAR(50),
    Especialidad_Nuev VARCHAR(50),
    Estado_Ant VARCHAR(20),
    Estado_Nuev VARCHAR(20),
    Cedula_Ant VARBINARY(MAX),
    Cedula_Nuev VARBINARY(MAX),
    Fecha_Evento DATETIME DEFAULT GETDATE()
);
GO

CREATE TABLE Auditoria_Cursos(
    Auditoria_Cur_ID INT IDENTITY(1,1) PRIMARY KEY,
    Curso_ID INT NOT NULL,
    Accion VARCHAR(10) NOT NULL,
    usuario_id INT NULL,
    usuario_nombre VARCHAR(100) NULL,
    Nombre_Ant VARCHAR(100),
    Nombre_Nuev VARCHAR(100),
    Categoria_Ant VARCHAR(50),
    Categoria_Nuev VARCHAR(50),
    Duracion_Ant INT,
    Duracion_Nuev INT,
    Costo_Ant DECIMAL(10,2),
    Costo_Nuev DECIMAL(10,2),
    Estado_Ant VARCHAR(20),
    Estado_Nuev VARCHAR(20),
    Fecha_Evento DATETIME DEFAULT GETDATE()
);
GO

CREATE TABLE Auditoria_Grupos(
    Auditoria_Gru_ID INT IDENTITY(1,1) PRIMARY KEY,
    Grupo_ID VARCHAR(20) NOT NULL,
    Accion VARCHAR(10) NOT NULL,
    usuario_id INT NULL,
    usuario_nombre VARCHAR(100) NULL,
    Curso_Ant INT,
    Curso_Nuev INT,
    Instructor_Ant INT,
    Instructor_Nuev INT,
    Cupo_Maximo_Ant INT,
    Cupo_Maximo_Nuev INT,
    Cupo_Disponible_Ant INT,
    Cupo_Disponible_Nuev INT,
    Fecha_Inicio_Ant DATE,
    Fecha_Inicio_Nuev DATE,
    Fecha_Evento DATETIME DEFAULT GETDATE()
);
GO

select* from Cursos
-- 9. SEGURIDAD Y CIFRADO


CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'Password123$Fuerte';
GO

CREATE CERTIFICATE CertificadoEducacion
WITH SUBJECT = 'Certificado para cifrado de datos de la plataforma';
GO

CREATE SYMMETRIC KEY ClaveEducacion
WITH ALGORITHM = AES_256
ENCRYPTION BY CERTIFICATE CertificadoEducacion;
GO


-- 10. INDICES


CREATE NONCLUSTERED INDEX Usuarios_Email ON Usuarios(email);
CREATE NONCLUSTERED INDEX Usuarios_Rol_Estado ON Usuarios(Rol_ID, Estado);
CREATE NONCLUSTERED INDEX Inscripciones_Estado_Fecha ON Inscripciones(Estado, Fecha_Inscripcion);
CREATE NONCLUSTERED INDEX Grupos_FechaInicio ON Grupos(Fecha_Inicio);
CREATE NONCLUSTERED INDEX Estudiantes_FechaRegistro ON Estudiantes(Fecha_Registro);
CREATE NONCLUSTERED INDEX Cursos_Estado ON Cursos(Estado);
CREATE NONCLUSTERED INDEX Pagos_Inscripcion ON Pagos(Inscripcion_ID);
CREATE NONCLUSTERED INDEX Evaluaciones_Inscripcion ON Evaluaciones(Inscripcion_ID);
GO


-- 11. FUNCION AUXILIAR


CREATE OR ALTER FUNCTION dbo.fn_GetUsuarioNombre(@usuario_id INT)
RETURNS VARCHAR(100)
AS
BEGIN
    DECLARE @nombre VARCHAR(100);
    
    SELECT @nombre = 
        CASE 
            WHEN u.Rol_ID = 1 THEN u.email
            WHEN u.Rol_ID = 2 THEN i.Nombre + ' ' + i.Apellidos
            WHEN u.Rol_ID = 3 THEN e.Nombre + ' ' + e.Apellidos
            ELSE SUSER_SNAME()
        END
    FROM Usuarios u
    LEFT JOIN Instructores i ON u.Usuario_ID = i.Usuario_ID
    LEFT JOIN Estudiantes e ON u.Usuario_ID = e.Usuario_ID
    WHERE u.Usuario_ID = @usuario_id;
    
    RETURN ISNULL(@nombre, SUSER_SNAME());
END;
GO


-- 12. TRIGGERS DE AUDITORIA (INSERT, UPDATE, DELETE)


-- TRIGGER AUDITORIA: ESTUDIANTES
CREATE OR ALTER TRIGGER trg_Auditoria_Estudiantes
ON Estudiantes
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @Accion VARCHAR(10);
    
    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        SET @Accion = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        SET @Accion = 'INSERT';
    ELSE
        SET @Accion = 'DELETE';
    
    IF @Accion = 'INSERT'
    BEGIN
        INSERT INTO Auditoria_Estudiantes (
            Estudiante_ID, Accion, usuario_id, usuario_nombre,
            Nombre_Ant, Nombre_Nuev, Apellidos_Ant, Apellidos_Nuev,
            Telefono_Ant, Telefono_Nuev, Direccion_Ant, Direccion_Nuev,
            Tipo_Documento_Ant, Tipo_Documento_Nuev, 
            Numero_Documento_Ant, Numero_Documento_Nuev
        )
        SELECT 
            i.Estudiante_ID, 'INSERT', i.Usuario_ID, dbo.fn_GetUsuarioNombre(i.Usuario_ID),
            NULL, i.Nombre, NULL, i.Apellidos,
            NULL, i.Telefono, NULL, i.Direccion,
            NULL, i.Tipo_Documento,
            NULL, i.Numero_Documento
        FROM inserted i;
    END
    
    IF @Accion = 'UPDATE'
    BEGIN
        INSERT INTO Auditoria_Estudiantes (
            Estudiante_ID, Accion, usuario_id, usuario_nombre,
            Nombre_Ant, Nombre_Nuev, Apellidos_Ant, Apellidos_Nuev,
            Telefono_Ant, Telefono_Nuev, Direccion_Ant, Direccion_Nuev,
            Tipo_Documento_Ant, Tipo_Documento_Nuev,
            Numero_Documento_Ant, Numero_Documento_Nuev
        )
        SELECT 
            i.Estudiante_ID, 'UPDATE', i.Usuario_ID, dbo.fn_GetUsuarioNombre(i.Usuario_ID),
            d.Nombre, i.Nombre, d.Apellidos, i.Apellidos,
            d.Telefono, i.Telefono, d.Direccion, i.Direccion,
            d.Tipo_Documento, i.Tipo_Documento,
            d.Numero_Documento, i.Numero_Documento
        FROM inserted i
        INNER JOIN deleted d ON i.Estudiante_ID = d.Estudiante_ID;
    END
    
    IF @Accion = 'DELETE'
    BEGIN
        INSERT INTO Auditoria_Estudiantes (
            Estudiante_ID, Accion, usuario_id, usuario_nombre,
            Nombre_Ant, Nombre_Nuev, Apellidos_Ant, Apellidos_Nuev,
            Telefono_Ant, Telefono_Nuev, Direccion_Ant, Direccion_Nuev,
            Tipo_Documento_Ant, Tipo_Documento_Nuev,
            Numero_Documento_Ant, Numero_Documento_Nuev
        )
        SELECT 
            d.Estudiante_ID, 'DELETE', d.Usuario_ID, dbo.fn_GetUsuarioNombre(d.Usuario_ID),
            d.Nombre, NULL, d.Apellidos, NULL,
            d.Telefono, NULL, d.Direccion, NULL,
            d.Tipo_Documento, NULL,
            d.Numero_Documento, NULL
        FROM deleted d;
    END
END;
GO

-- TRIGGER AUDITORIA: INSTRUCTORES
CREATE OR ALTER TRIGGER trg_Auditoria_Instructores
ON Instructores
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @Accion VARCHAR(10);
    
    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        SET @Accion = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        SET @Accion = 'INSERT';
    ELSE
        SET @Accion = 'DELETE';
    
    IF @Accion = 'INSERT'
    BEGIN
        INSERT INTO Auditoria_Instructores (
            Instructor_ID, Accion, usuario_id, usuario_nombre,
            Nombre_Ant, Nombre_Nuev, Apellidos_Ant, Apellidos_Nuev,
            Especialidad_Ant, Especialidad_Nuev, Estado_Ant, Estado_Nuev,
            Cedula_Ant, Cedula_Nuev
        )
        SELECT 
            i.Instructor_ID, 'INSERT', i.Usuario_ID, dbo.fn_GetUsuarioNombre(i.Usuario_ID),
            NULL, i.Nombre, NULL, i.Apellidos,
            NULL, i.Especialidad, NULL, i.Estado,
            NULL, i.Cedula_Profesional
        FROM inserted i;
    END
    
    IF @Accion = 'UPDATE'
    BEGIN
        INSERT INTO Auditoria_Instructores (
            Instructor_ID, Accion, usuario_id, usuario_nombre,
            Nombre_Ant, Nombre_Nuev, Apellidos_Ant, Apellidos_Nuev,
            Especialidad_Ant, Especialidad_Nuev, Estado_Ant, Estado_Nuev,
            Cedula_Ant, Cedula_Nuev
        )
        SELECT 
            i.Instructor_ID, 'UPDATE', i.Usuario_ID, dbo.fn_GetUsuarioNombre(i.Usuario_ID),
            d.Nombre, i.Nombre, d.Apellidos, i.Apellidos,
            d.Especialidad, i.Especialidad, d.Estado, i.Estado,
            d.Cedula_Profesional, i.Cedula_Profesional
        FROM inserted i
        INNER JOIN deleted d ON i.Instructor_ID = d.Instructor_ID;
    END
    
    IF @Accion = 'DELETE'
    BEGIN
        INSERT INTO Auditoria_Instructores (
            Instructor_ID, Accion, usuario_id, usuario_nombre,
            Nombre_Ant, Nombre_Nuev, Apellidos_Ant, Apellidos_Nuev,
            Especialidad_Ant, Especialidad_Nuev, Estado_Ant, Estado_Nuev,
            Cedula_Ant, Cedula_Nuev
        )
        SELECT 
            d.Instructor_ID, 'DELETE', d.Usuario_ID, dbo.fn_GetUsuarioNombre(d.Usuario_ID),
            d.Nombre, NULL, d.Apellidos, NULL,
            d.Especialidad, NULL, d.Estado, NULL,
            d.Cedula_Profesional, NULL
        FROM deleted d;
    END
END;
GO

-- TRIGGER AUDITORIA: CURSOS
CREATE OR ALTER TRIGGER trg_Auditoria_Cursos
ON Cursos
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @Accion VARCHAR(10);
    
    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        SET @Accion = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        SET @Accion = 'INSERT';
    ELSE
        SET @Accion = 'DELETE';
    
    IF @Accion = 'INSERT'
    BEGIN
        INSERT INTO Auditoria_Cursos (
            Curso_ID, Accion, usuario_id, usuario_nombre,
            Nombre_Ant, Nombre_Nuev, Categoria_Ant, Categoria_Nuev,
            Duracion_Ant, Duracion_Nuev, Costo_Ant, Costo_Nuev,
            Estado_Ant, Estado_Nuev
        )
        SELECT 
            i.Curso_ID, 'INSERT', NULL, SUSER_SNAME(),
            NULL, i.Nombre_Curso, NULL, i.Categoria,
            NULL, i.Duracion_Horas, NULL, i.Costo,
            NULL, i.Estado
        FROM inserted i;
    END
    
    IF @Accion = 'UPDATE'
    BEGIN
        INSERT INTO Auditoria_Cursos (
            Curso_ID, Accion, usuario_id, usuario_nombre,
            Nombre_Ant, Nombre_Nuev, Categoria_Ant, Categoria_Nuev,
            Duracion_Ant, Duracion_Nuev, Costo_Ant, Costo_Nuev,
            Estado_Ant, Estado_Nuev
        )
        SELECT 
            i.Curso_ID, 'UPDATE', NULL, SUSER_SNAME(),
            d.Nombre_Curso, i.Nombre_Curso, d.Categoria, i.Categoria,
            d.Duracion_Horas, i.Duracion_Horas, d.Costo, i.Costo,
            d.Estado, i.Estado
        FROM inserted i
        INNER JOIN deleted d ON i.Curso_ID = d.Curso_ID;
    END
    
    IF @Accion = 'DELETE'
    BEGIN
        INSERT INTO Auditoria_Cursos (
            Curso_ID, Accion, usuario_id, usuario_nombre,
            Nombre_Ant, Nombre_Nuev, Categoria_Ant, Categoria_Nuev,
            Duracion_Ant, Duracion_Nuev, Costo_Ant, Costo_Nuev,
            Estado_Ant, Estado_Nuev
        )
        SELECT 
            d.Curso_ID, 'DELETE', NULL, SUSER_SNAME(),
            d.Nombre_Curso, NULL, d.Categoria, NULL,
            d.Duracion_Horas, NULL, d.Costo, NULL,
            d.Estado, NULL
        FROM deleted d;
    END
END;
GO

-- TRIGGER AUDITORIA: GRUPOS
CREATE OR ALTER TRIGGER trg_Auditoria_Grupos
ON Grupos
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @Accion VARCHAR(10);
    
    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        SET @Accion = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        SET @Accion = 'INSERT';
    ELSE
        SET @Accion = 'DELETE';
    
    IF @Accion = 'INSERT'
    BEGIN
        INSERT INTO Auditoria_Grupos (
            Grupo_ID, Accion, usuario_id, usuario_nombre,
            Curso_Ant, Curso_Nuev, Instructor_Ant, Instructor_Nuev,
            Cupo_Maximo_Ant, Cupo_Maximo_Nuev, 
            Cupo_Disponible_Ant, Cupo_Disponible_Nuev,
            Fecha_Inicio_Ant, Fecha_Inicio_Nuev
        )
        SELECT 
            i.Grupo_ID, 'INSERT', NULL, SUSER_SNAME(),
            NULL, i.Curso_ID, NULL, i.Instructor_ID,
            NULL, i.Cupo_Maximo,
            NULL, i.Cupo_Disponible,
            NULL, i.Fecha_Inicio
        FROM inserted i;
    END
    
    IF @Accion = 'UPDATE'
    BEGIN
        INSERT INTO Auditoria_Grupos (
            Grupo_ID, Accion, usuario_id, usuario_nombre,
            Curso_Ant, Curso_Nuev, Instructor_Ant, Instructor_Nuev,
            Cupo_Maximo_Ant, Cupo_Maximo_Nuev, 
            Cupo_Disponible_Ant, Cupo_Disponible_Nuev,
            Fecha_Inicio_Ant, Fecha_Inicio_Nuev
        )
        SELECT 
            i.Grupo_ID, 'UPDATE', NULL, SUSER_SNAME(),
            d.Curso_ID, i.Curso_ID, d.Instructor_ID, i.Instructor_ID,
            d.Cupo_Maximo, i.Cupo_Maximo,
            d.Cupo_Disponible, i.Cupo_Disponible,
            d.Fecha_Inicio, i.Fecha_Inicio
        FROM inserted i
        INNER JOIN deleted d ON i.Grupo_ID = d.Grupo_ID;
    END
    
    IF @Accion = 'DELETE'
    BEGIN
        INSERT INTO Auditoria_Grupos (
            Grupo_ID, Accion, usuario_id, usuario_nombre,
            Curso_Ant, Curso_Nuev, Instructor_Ant, Instructor_Nuev,
            Cupo_Maximo_Ant, Cupo_Maximo_Nuev, 
            Cupo_Disponible_Ant, Cupo_Disponible_Nuev,
            Fecha_Inicio_Ant, Fecha_Inicio_Nuev
        )
        SELECT 
            d.Grupo_ID, 'DELETE', NULL, SUSER_SNAME(),
            d.Curso_ID, NULL, d.Instructor_ID, NULL,
            d.Cupo_Maximo, NULL,
            d.Cupo_Disponible, NULL,
            d.Fecha_Inicio, NULL
        FROM deleted d;
    END
END;
GO

-- TRIGGER AUDITORIA: INSCRIPCIONES
CREATE OR ALTER TRIGGER trg_Auditoria_Inscripciones
ON Inscripciones
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @Accion VARCHAR(10);
    
    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        SET @Accion = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        SET @Accion = 'INSERT';
    ELSE
        SET @Accion = 'DELETE';
    
    IF @Accion = 'INSERT'
    BEGIN
        INSERT INTO Auditoria_Inscripciones (
            Inscripcion_ID, Accion, usuario_id, usuario_nombre,
            edo_ant, edo_nuevo, total_pago_anterior, total_pago_nuevo
        )
        SELECT 
            i.Inscripcion_ID, 'INSERT', 
            i.Estudiante_ID, 
            (SELECT e.Nombre + ' ' + e.Apellidos FROM Estudiantes e WHERE e.Estudiante_ID = i.Estudiante_ID),
            NULL, i.Estado, NULL, i.Total_Pago
        FROM inserted i;
    END
    
    IF @Accion = 'UPDATE'
    BEGIN
        INSERT INTO Auditoria_Inscripciones (
            Inscripcion_ID, Accion, usuario_id, usuario_nombre,
            edo_ant, edo_nuevo, total_pago_anterior, total_pago_nuevo
        )
        SELECT 
            i.Inscripcion_ID, 'UPDATE',
            i.Estudiante_ID,
            (SELECT e.Nombre + ' ' + e.Apellidos FROM Estudiantes e WHERE e.Estudiante_ID = i.Estudiante_ID),
            d.Estado, i.Estado, d.Total_Pago, i.Total_Pago
        FROM inserted i
        INNER JOIN deleted d ON i.Inscripcion_ID = d.Inscripcion_ID;
    END
    
    IF @Accion = 'DELETE'
    BEGIN
        INSERT INTO Auditoria_Inscripciones (
            Inscripcion_ID, Accion, usuario_id, usuario_nombre,
            edo_ant, edo_nuevo, total_pago_anterior, total_pago_nuevo
        )
        SELECT 
            d.Inscripcion_ID, 'DELETE',
            d.Estudiante_ID,
            (SELECT e.Nombre + ' ' + e.Apellidos FROM Estudiantes e WHERE e.Estudiante_ID = d.Estudiante_ID),
            d.Estado, NULL, d.Total_Pago, NULL
        FROM deleted d;
    END
END;
GO

-- TRIGGER AUDITORIA: EVALUACIONES
CREATE OR ALTER TRIGGER trg_Auditoria_Evaluaciones
ON Evaluaciones
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @Accion VARCHAR(10);
    
    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        SET @Accion = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        SET @Accion = 'INSERT';
    ELSE
        SET @Accion = 'DELETE';
    
    IF @Accion = 'INSERT'
    BEGIN
        INSERT INTO Auditoria_Evaluaciones (
            Evaluacion_ID, Accion, usuario_id, usuario_nombre,
            cal_ante, cal_nuev, coment_ant, coment_nuev
        )
        SELECT 
            i.Evaluacion_ID, 'INSERT', NULL, SUSER_SNAME(),
            NULL, i.Calificacion, NULL, i.Comentarios
        FROM inserted i;
    END
    
    IF @Accion = 'UPDATE'
    BEGIN
        INSERT INTO Auditoria_Evaluaciones (
            Evaluacion_ID, Accion, usuario_id, usuario_nombre,
            cal_ante, cal_nuev, coment_ant, coment_nuev
        )
        SELECT 
            i.Evaluacion_ID, 'UPDATE', NULL, SUSER_SNAME(),
            d.Calificacion, i.Calificacion, d.Comentarios, i.Comentarios
        FROM inserted i
        INNER JOIN deleted d ON i.Evaluacion_ID = d.Evaluacion_ID;
    END
    
    IF @Accion = 'DELETE'
    BEGIN
        INSERT INTO Auditoria_Evaluaciones (
            Evaluacion_ID, Accion, usuario_id, usuario_nombre,
            cal_ante, cal_nuev, coment_ant, coment_nuev
        )
        SELECT 
            d.Evaluacion_ID, 'DELETE', NULL, SUSER_SNAME(),
            d.Calificacion, NULL, d.Comentarios, NULL
        FROM deleted d;
    END
END;
GO

-- TRIGGER AUDITORIA: PAGOS
CREATE OR ALTER TRIGGER trg_Auditoria_Pagos
ON Pagos
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @Accion VARCHAR(10);
    
    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        SET @Accion = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        SET @Accion = 'INSERT';
    ELSE
        SET @Accion = 'DELETE';
    
    IF @Accion = 'INSERT'
    BEGIN
        INSERT INTO Auditoria_Pagos (
            Pago_ID, Accion, usuario_id, usuario_nombre,
            Monto_ant, Monto_nuev, Referencia_pago_ant, Referencia_pago_nuev
        )
        SELECT 
            i.Pagos_ID, 'INSERT', NULL, SUSER_SNAME(),
            NULL, i.Monto, NULL, i.Referencia_Pago
        FROM inserted i;
    END
    
    IF @Accion = 'UPDATE'
    BEGIN
        INSERT INTO Auditoria_Pagos (
            Pago_ID, Accion, usuario_id, usuario_nombre,
            Monto_ant, Monto_nuev, Referencia_pago_ant, Referencia_pago_nuev
        )
        SELECT 
            i.Pagos_ID, 'UPDATE', NULL, SUSER_SNAME(),
            d.Monto, i.Monto, d.Referencia_Pago, i.Referencia_Pago
        FROM inserted i
        INNER JOIN deleted d ON i.Pagos_ID = d.Pagos_ID;
    END
    
    IF @Accion = 'DELETE'
    BEGIN
        INSERT INTO Auditoria_Pagos (
            Pago_ID, Accion, usuario_id, usuario_nombre,
            Monto_ant, Monto_nuev, Referencia_pago_ant, Referencia_pago_nuev
        )
        SELECT 
            d.Pagos_ID, 'DELETE', NULL, SUSER_SNAME(),
            d.Monto, NULL, d.Referencia_Pago, NULL
        FROM deleted d;
    END
END;
GO

-- TRIGGER AUDITORIA: ENTREGAS
CREATE OR ALTER TRIGGER trg_Auditoria_Entregas
ON Entregas
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @Accion VARCHAR(10);
    
    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        SET @Accion = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        SET @Accion = 'INSERT';
    ELSE
        SET @Accion = 'DELETE';
    
    IF @Accion = 'INSERT'
    BEGIN
        INSERT INTO Auditoria_Entregas (
            Entrega_ID, Accion, usuario_id, usuario_nombre,
            Archivo_Ant, Archivo_Nuev, Comentario_Ant, Comentario_Nuev,
            Calificacion_Ant, Calificacion_Nuev
        )
        SELECT 
            i.Entrega_ID, 'INSERT', NULL, SUSER_SNAME(),
            NULL, i.Archivo, NULL, i.Comentario,
            NULL, i.Calificacion
        FROM inserted i;
    END
    
    IF @Accion = 'UPDATE'
    BEGIN
        INSERT INTO Auditoria_Entregas (
            Entrega_ID, Accion, usuario_id, usuario_nombre,
            Archivo_Ant, Archivo_Nuev, Comentario_Ant, Comentario_Nuev,
            Calificacion_Ant, Calificacion_Nuev
        )
        SELECT 
            i.Entrega_ID, 'UPDATE', NULL, SUSER_SNAME(),
            d.Archivo, i.Archivo, d.Comentario, i.Comentario,
            d.Calificacion, i.Calificacion
        FROM inserted i
        INNER JOIN deleted d ON i.Entrega_ID = d.Entrega_ID;
    END
    
    IF @Accion = 'DELETE'
    BEGIN
        INSERT INTO Auditoria_Entregas (
            Entrega_ID, Accion, usuario_id, usuario_nombre,
            Archivo_Ant, Archivo_Nuev, Comentario_Ant, Comentario_Nuev,
            Calificacion_Ant, Calificacion_Nuev
        )
        SELECT 
            d.Entrega_ID, 'DELETE', NULL, SUSER_SNAME(),
            d.Archivo, NULL, d.Comentario, NULL,
            d.Calificacion, NULL
        FROM deleted d;
    END
END;
GO

-- 13. TRIGGER CONTROL DE CUPO


CREATE OR ALTER TRIGGER trg_Control_Cupo_Inscripciones
ON Inscripciones
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @Grupo_ID VARCHAR(20);
    DECLARE @Cupo_Disponible INT;
    
    SELECT @Grupo_ID = Grupo_ID FROM inserted;
    SELECT @Cupo_Disponible = Cupo_Disponible FROM Grupos WHERE Grupo_ID = @Grupo_ID;
    
    IF @Cupo_Disponible = 0
    BEGIN
        UPDATE Cursos SET Estado = 'Lleno' 
        WHERE Curso_ID = (SELECT Curso_ID FROM Grupos WHERE Grupo_ID = @Grupo_ID);
    END
END;
GO


-- 14. PROCEDIMIENTOS ALMACENADOS


CREATE OR ALTER PROCEDURE Registrar_Estudiante
    @Email VARCHAR(100),
    @Contrasena VARCHAR(100), 
    @Nombre VARCHAR(100),
    @Apellidos VARCHAR(100),
    @Direccion VARCHAR(150),
    @Telefono VARCHAR(20),
    @Tipo_Documento VARCHAR(20),
    @Numero_Documento VARCHAR(50) 
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        OPEN SYMMETRIC KEY ClaveEducacion DECRYPTION BY CERTIFICATE CertificadoEducacion;
        
        DECLARE @Nuevo_Usuario_ID INT;
        INSERT INTO Usuarios (Rol_ID, email, Contrasena, Estado)
        VALUES (3, @Email, EncryptByKey(Key_GUID('ClaveEducacion'), @Contrasena), 'Activo');
        SET @Nuevo_Usuario_ID = SCOPE_IDENTITY();

        INSERT INTO Estudiantes (Usuario_ID, Nombre, Apellidos, Direccion, Telefono, Tipo_Documento, Numero_Documento)
        VALUES (@Nuevo_Usuario_ID, @Nombre, @Apellidos, @Direccion, @Telefono, @Tipo_Documento, 
                EncryptByKey(Key_GUID('ClaveEducacion'), @Numero_Documento));

        CLOSE SYMMETRIC KEY ClaveEducacion;
        COMMIT TRANSACTION;
        PRINT 'Estudiante registrado correctamente.';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK;
        IF EXISTS (SELECT 1 FROM sys.openkeys WHERE key_name = 'ClaveEducacion') CLOSE SYMMETRIC KEY ClaveEducacion;
        INSERT INTO Bitacora_Errores (Numero_Error, Mensaje_Error, Procedimiento, Linea_Error)
        VALUES (ERROR_NUMBER(), ERROR_MESSAGE(), 'Registrar_Estudiante', ERROR_LINE());
        PRINT ERROR_MESSAGE();
    END CATCH
END;
GO

CREATE OR ALTER PROCEDURE Registrar_Instructor
    @Email VARCHAR(100),
    @Contrasena VARCHAR(100),
    @Nombre VARCHAR(50),
    @Apellidos VARCHAR(50),
    @Especialidad VARCHAR(50),
    @Cedula_Profesional VARCHAR(50),
    @Estado VARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        OPEN SYMMETRIC KEY ClaveEducacion DECRYPTION BY CERTIFICATE CertificadoEducacion;
        
        DECLARE @Nuevo_Usuario_ID INT;
        INSERT INTO Usuarios (Rol_ID, email, Contrasena, Estado)
        VALUES (2, @Email, EncryptByKey(Key_GUID('ClaveEducacion'), @Contrasena), @Estado);
        SET @Nuevo_Usuario_ID = SCOPE_IDENTITY();

        INSERT INTO Instructores (Usuario_ID, Nombre, Apellidos, Especialidad, Cedula_Profesional, Estado)
        VALUES (@Nuevo_Usuario_ID, @Nombre, @Apellidos, @Especialidad, 
                EncryptByKey(Key_GUID('ClaveEducacion'), @Cedula_Profesional), @Estado);

        CLOSE SYMMETRIC KEY ClaveEducacion;
        COMMIT TRANSACTION;
        PRINT 'Instructor registrado correctamente.';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK;
        IF EXISTS (SELECT 1 FROM sys.openkeys WHERE key_name = 'ClaveEducacion') CLOSE SYMMETRIC KEY ClaveEducacion;
        INSERT INTO Bitacora_Errores (Numero_Error, Mensaje_Error, Procedimiento, Linea_Error)
        VALUES (ERROR_NUMBER(), ERROR_MESSAGE(), 'Registrar_Instructor', ERROR_LINE());
        PRINT ERROR_MESSAGE();
    END CATCH
END;
GO

CREATE OR ALTER PROCEDURE Registrar_Curso
    @Nombre_Curso VARCHAR(100),
    @Categoria VARCHAR(50),
    @Duracion_Horas INT,
    @Costo DECIMAL(10,2),
    @Estado VARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        INSERT INTO Cursos (Nombre_Curso, Categoria, Duracion_Horas, Costo, Estado)
        VALUES (@Nombre_Curso, @Categoria, @Duracion_Horas, @Costo, @Estado);
        COMMIT TRANSACTION;
        PRINT 'Curso registrado correctamente.';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK;
        INSERT INTO Bitacora_Errores (Numero_Error, Mensaje_Error, Procedimiento, Linea_Error)
        VALUES (ERROR_NUMBER(), ERROR_MESSAGE(), 'Registrar_Curso', ERROR_LINE());
        PRINT ERROR_MESSAGE();
    END CATCH
END;
GO

CREATE OR ALTER PROCEDURE Registrar_Grupo
    @Curso_ID INT,
    @Instructor_ID INT,
    @Cupo_Maximo INT,
    @Fecha_Inicio DATE
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        
        IF NOT EXISTS (SELECT 1 FROM Cursos WHERE Curso_ID = @Curso_ID AND Estado = 'Activo')
        BEGIN
            RAISERROR('El curso no existe o no esta activo.', 16, 1);
            RETURN;
        END
        
        IF NOT EXISTS (SELECT 1 FROM Instructores WHERE Instructor_ID = @Instructor_ID AND Estado = 'Activo')
        BEGIN
            RAISERROR('El instructor no existe o no esta activo.', 16, 1);
            RETURN;
        END

        INSERT INTO Grupos (Curso_ID, Instructor_ID, Cupo_Maximo, Cupo_Disponible, Fecha_Inicio)
        VALUES (@Curso_ID, @Instructor_ID, @Cupo_Maximo, @Cupo_Maximo, @Fecha_Inicio);
        
        COMMIT TRANSACTION;
        PRINT 'Grupo registrado correctamente.';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK;
        INSERT INTO Bitacora_Errores (Numero_Error, Mensaje_Error, Procedimiento, Linea_Error)
        VALUES (ERROR_NUMBER(), ERROR_MESSAGE(), 'Registrar_Grupo', ERROR_LINE());
        PRINT ERROR_MESSAGE();
    END CATCH
END;
GO

CREATE OR ALTER PROCEDURE Registrar_Inscripcion
    @Estudiante_ID INT,
    @Grupo_ID VARCHAR(20),
    @Total_Pago DECIMAL(10,2)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        
        IF NOT EXISTS (SELECT 1 FROM Estudiantes WHERE Estudiante_ID = @Estudiante_ID)
        BEGIN
            RAISERROR('El estudiante no existe.', 16, 1);
            RETURN;
        END
        
        DECLARE @Cupo_Disponible INT;
        SELECT @Cupo_Disponible = Cupo_Disponible FROM Grupos WHERE Grupo_ID = @Grupo_ID;
        
        IF @Cupo_Disponible IS NULL
        BEGIN
            RAISERROR('El grupo no existe.', 16, 1);
            RETURN;
        END
        
        IF @Cupo_Disponible <= 0
        BEGIN
            RAISERROR('No hay cupo disponible en este grupo.', 16, 1);
            RETURN;
        END
        
        UPDATE Grupos SET Cupo_Disponible = Cupo_Disponible - 1 WHERE Grupo_ID = @Grupo_ID;
        
        INSERT INTO Inscripciones (Estudiante_ID, Grupo_ID, Total_Pago, Estado, Fecha_Inscripcion)
        VALUES (@Estudiante_ID, @Grupo_ID, @Total_Pago, 'Activa', GETDATE());
        
        DECLARE @Inscripcion_ID INT = SCOPE_IDENTITY();
        
        IF @Inscripcion_ID IS NULL
        BEGIN
            RAISERROR('Error al obtener el ID de inscripcion.', 16, 1);
            RETURN;
        END
        
        OPEN SYMMETRIC KEY ClaveEducacion DECRYPTION BY CERTIFICATE CertificadoEducacion;
        
        INSERT INTO Pagos (Inscripcion_ID, Metodo_Pago, Monto, Referencia_Pago, Fecha_Pago)
        VALUES (@Inscripcion_ID, 'Automatico', @Total_Pago, 
                EncryptByKey(Key_GUID('ClaveEducacion'), CONCAT('AUTO-', CAST(@Inscripcion_ID AS VARCHAR(20)))), 
                GETDATE());
        
        CLOSE SYMMETRIC KEY ClaveEducacion;
        
        COMMIT TRANSACTION;
        PRINT 'Inscripcion registrada exitosamente. ID: ' + CAST(@Inscripcion_ID AS VARCHAR);
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK;
        IF EXISTS (SELECT 1 FROM sys.openkeys WHERE key_name = 'ClaveEducacion') CLOSE SYMMETRIC KEY ClaveEducacion;
        INSERT INTO Bitacora_Errores (Numero_Error, Mensaje_Error, Procedimiento, Linea_Error)
        VALUES (ERROR_NUMBER(), ERROR_MESSAGE(), 'Registrar_Inscripcion', ERROR_LINE());
        PRINT ERROR_MESSAGE();
    END CATCH
END;
GO

CREATE OR ALTER PROCEDURE Registrar_Evaluacion
    @Inscripcion_ID INT,
    @Calificacion DECIMAL(5,2),
    @Comentario VARCHAR(500)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        
        IF NOT EXISTS (SELECT 1 FROM Inscripciones WHERE Inscripcion_ID = @Inscripcion_ID)
        BEGIN
            RAISERROR('La inscripcion no existe.', 16, 1);
            RETURN;
        END
        
        OPEN SYMMETRIC KEY ClaveEducacion DECRYPTION BY CERTIFICATE CertificadoEducacion;

        INSERT INTO Evaluaciones (Inscripcion_ID, Calificacion, Comentarios)
        VALUES (@Inscripcion_ID, @Calificacion, 
                CASE WHEN @Comentario IS NOT NULL THEN EncryptByKey(Key_GUID('ClaveEducacion'), @Comentario) ELSE NULL END);

        CLOSE SYMMETRIC KEY ClaveEducacion;
        COMMIT TRANSACTION;
        PRINT 'Evaluacion registrada correctamente.';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK;
        IF EXISTS (SELECT 1 FROM sys.openkeys WHERE key_name = 'ClaveEducacion') CLOSE SYMMETRIC KEY ClaveEducacion;
        INSERT INTO Bitacora_Errores (Numero_Error, Mensaje_Error, Procedimiento, Linea_Error)
        VALUES (ERROR_NUMBER(), ERROR_MESSAGE(), 'Registrar_Evaluacion', ERROR_LINE());
        PRINT ERROR_MESSAGE();
    END CATCH
END;
GO


-- 15. INSERTAR DATOS DE PRUEBA


INSERT INTO Roles_Usuario (Nombre_Rol) VALUES 
('Administrador'), 
('Instructor'),
('Estudiante');
GO

OPEN SYMMETRIC KEY ClaveEducacion DECRYPTION BY CERTIFICATE CertificadoEducacion;                

INSERT INTO Usuarios (Rol_ID, email, Contrasena, Estado)
VALUES 
(2, 'alan.turing@edu.com', EncryptByKey(Key_GUID('ClaveEducacion'), 'InstPass01'), 'Activo'),
(2, 'ada.lovelace@edu.com', EncryptByKey(Key_GUID('ClaveEducacion'), 'InstPass02'), 'Activo'),
(2, 'j.hernandez@edu.com', EncryptByKey(Key_GUID('ClaveEducacion'), 'InstPass03'), 'Activo'),
(2, 'm.garcia@edu.com', EncryptByKey(Key_GUID('ClaveEducacion'), 'InstPass04'), 'Activo'),
(2, 'r.silva@edu.com', EncryptByKey(Key_GUID('ClaveEducacion'), 'InstPass05'), 'Activo'),
(2, 'c.lopez@edu.com', EncryptByKey(Key_GUID('ClaveEducacion'), 'InstPass06'), 'Activo'),
(2, 'a.martinez@edu.com', EncryptByKey(Key_GUID('ClaveEducacion'), 'InstPass07'), 'Activo'),
(2, 'v.rodriguez@edu.com', EncryptByKey(Key_GUID('ClaveEducacion'), 'InstPass08'), 'Activo'),
(2, 'd.fernandez@edu.com', EncryptByKey(Key_GUID('ClaveEducacion'), 'InstPass09'), 'Activo'),
(2, 's.perez@edu.com', EncryptByKey(Key_GUID('ClaveEducacion'), 'InstPass10'), 'Activo');

INSERT INTO Instructores (Usuario_ID, Nombre, Apellidos, Especialidad, Cedula_Profesional, Estado) 
VALUES 
((SELECT Usuario_ID FROM Usuarios WHERE email = 'alan.turing@edu.com'), 'Alan', 'Turing', 'Criptografia', EncryptByKey(Key_GUID('ClaveEducacion'), 'CED-9991'), 'Activo'),
((SELECT Usuario_ID FROM Usuarios WHERE email = 'ada.lovelace@edu.com'), 'Ada', 'Lovelace', 'Programacion', EncryptByKey(Key_GUID('ClaveEducacion'), 'CED-9992'), 'Activo'),
((SELECT Usuario_ID FROM Usuarios WHERE email = 'j.hernandez@edu.com'), 'Jorge', 'Hernandez', 'Redes', EncryptByKey(Key_GUID('ClaveEducacion'), 'CED-9993'), 'Activo'),
((SELECT Usuario_ID FROM Usuarios WHERE email = 'm.garcia@edu.com'), 'Maria', 'Garcia', 'Inteligencia Artificial', EncryptByKey(Key_GUID('ClaveEducacion'), 'CED-9994'), 'Activo'),
((SELECT Usuario_ID FROM Usuarios WHERE email = 'r.silva@edu.com'), 'Roberto', 'Silva', 'Bases de Datos', EncryptByKey(Key_GUID('ClaveEducacion'), 'CED-9995'), 'Activo'),
((SELECT Usuario_ID FROM Usuarios WHERE email = 'c.lopez@edu.com'), 'Carmen', 'Lopez', 'Frontend', EncryptByKey(Key_GUID('ClaveEducacion'), 'CED-9996'), 'Activo'),
((SELECT Usuario_ID FROM Usuarios WHERE email = 'a.martinez@edu.com'), 'Alejandro', 'Martinez', 'DevOps', EncryptByKey(Key_GUID('ClaveEducacion'), 'CED-9997'), 'Activo'),
((SELECT Usuario_ID FROM Usuarios WHERE email = 'v.rodriguez@edu.com'), 'Veronica', 'Rodriguez', 'Ciberseguridad', EncryptByKey(Key_GUID('ClaveEducacion'), 'CED-9998'), 'Activo'),
((SELECT Usuario_ID FROM Usuarios WHERE email = 'd.fernandez@edu.com'), 'Daniel', 'Fernandez', 'Arquitectura de Software', EncryptByKey(Key_GUID('ClaveEducacion'), 'CED-9999'), 'Activo'),
((SELECT Usuario_ID FROM Usuarios WHERE email = 's.perez@edu.com'), 'Sofia', 'Perez', 'Metodologias Agiles', EncryptByKey(Key_GUID('ClaveEducacion'), 'CED-10000'), 'Activo');

CLOSE SYMMETRIC KEY ClaveEducacion;
GO
SELECT* FROM Estudiantes
INSERT INTO Cursos (Nombre_Curso, Categoria, Duracion_Horas, Costo, Estado) 
VALUES 
('Seguridad en Bases de Datos', 'Ciberseguridad', 40, 1500.00, 'Activo'),
('Backend con Python', 'Programacion', 60, 2000.00, 'Activo'),
('Fundamentos de Redes CISCO', 'Redes', 50, 1800.00, 'Activo'),
('Machine Learning Avanzado', 'Inteligencia Artificial', 60, 2500.00, 'Activo'),
('Tuning de Consultas SQL', 'Bases de Datos', 30, 1200.00, 'Activo'),
('React y Arquitectura Frontend', 'Frontend', 45, 1600.00, 'Activo'),
('Integracion Continua con Docker', 'DevOps', 40, 1900.00, 'Activo'),
('Ethical Hacking y Pentesting', 'Ciberseguridad', 55, 2200.00, 'Activo'),
('Patrones de Diseno Microservicios', 'Arquitectura de Software', 40, 2100.00, 'Activo'),
('Scrum Master Certificacion', 'Metodologias Agiles', 25, 1100.00, 'Activo');
GO

ALTER SEQUENCE Seq_Grupo RESTART WITH 1;
GO

INSERT INTO Grupos (Curso_ID, Instructor_ID, Cupo_Maximo, Cupo_Disponible, Fecha_Inicio) 
VALUES 
(1, 1, 30, 30, '2026-05-01'),
(2, 2, 5, 5, '2026-06-01'),
(3, 3, 25, 25, '2026-07-01'),
(4, 4, 20, 20, '2026-07-15'),
(5, 5, 30, 30, '2026-08-01'),
(6, 6, 30, 30, '2026-08-10'),
(7, 7, 15, 15, '2026-09-01'),
(8, 8, 20, 20, '2026-09-15'),
(9, 9, 25, 25, '2026-10-01'),
(10, 10, 40, 40, '2026-10-15');
GO

EXEC Registrar_Estudiante 'est1@edu.com', '1234566', 'Carlos', 'Ramirez', 'Calle Sol 45', '5550015689', 'INE', 'DOC-001';
EXEC Registrar_Estudiante 'est2@edu.com', '1324657', 'Lucia', 'Gomez', 'Calle Luna 123', '5550021259', 'INE', 'DOC-002';
EXEC Registrar_Estudiante 'est3@edu.com', '4679135', 'Marcos', 'Perez', 'Calle Penaflor 51', '5550038525', 'Pasaporte', 'DOC-003';
EXEC Registrar_Estudiante 'est4@edu.com', '9638527', 'Sofia', 'Ruiz', 'Calle Arquitectos 78', '5550044976', 'INE', 'DOC-004';
EXEC Registrar_Estudiante 'est5@edu.com', '7418529', 'Jorge', 'Diaz', 'Calle Otilio Montano 34', '5550057649', 'INE', 'DOC-005';
EXEC Registrar_Estudiante 'est6@edu.com', '1237894', 'Elena', 'Torres', 'Calle Rodrigo Diaz 12', '5550061634', 'Pasaporte', 'DOC-006';
EXEC Registrar_Estudiante 'est7@edu.com', '7946135', 'Raul', 'Vargas', 'Calle Belarousse 267', '5550071973', 'INE', 'DOC-007';
EXEC Registrar_Estudiante 'est8@edu.com', '3164975', 'Diana', 'Castro', 'Calle Montenes 124', '5550085689', 'INE', 'DOC-008';
EXEC Registrar_Estudiante 'est9@edu.com', '1728396', 'Mario', 'Rios', 'Calle Nueva Ampliacion 567', '5550091245', 'INE', 'DOC-009';
EXEC Registrar_Estudiante 'est10@edu.com', '4589236', 'Ana', 'Molina', 'Calle Berlitz 456', '5550104679', 'Pasaporte', 'DOC-010';
GO

EXEC Registrar_Inscripcion 1, 'GRUPO-0001', 1500.00;
EXEC Registrar_Inscripcion 2, 'GRUPO-0001', 1500.00;
EXEC Registrar_Inscripcion 3, 'GRUPO-0002', 2000.00;
EXEC Registrar_Inscripcion 4, 'GRUPO-0002', 2000.00;
EXEC Registrar_Inscripcion 5, 'GRUPO-0003', 1800.00;
EXEC Registrar_Inscripcion 6, 'GRUPO-0004', 2500.00;
EXEC Registrar_Inscripcion 7, 'GRUPO-0005', 1200.00;
EXEC Registrar_Inscripcion 8, 'GRUPO-0006', 1600.00;
EXEC Registrar_Inscripcion 9, 'GRUPO-0007', 1900.00;
EXEC Registrar_Inscripcion 10, 'GRUPO-0008', 2200.00;
GO

DECLARE @Ins1 INT, @Ins2 INT, @Ins3 INT, @Ins4 INT, @Ins5 INT;
DECLARE @Ins6 INT, @Ins7 INT, @Ins8 INT, @Ins9 INT, @Ins10 INT;

SELECT @Ins1 = MIN(Inscripcion_ID) FROM Inscripciones;
SELECT @Ins2 = MIN(Inscripcion_ID) FROM Inscripciones WHERE Inscripcion_ID > @Ins1;
SELECT @Ins3 = MIN(Inscripcion_ID) FROM Inscripciones WHERE Inscripcion_ID > @Ins2;
SELECT @Ins4 = MIN(Inscripcion_ID) FROM Inscripciones WHERE Inscripcion_ID > @Ins3;
SELECT @Ins5 = MIN(Inscripcion_ID) FROM Inscripciones WHERE Inscripcion_ID > @Ins4;
SELECT @Ins6 = MIN(Inscripcion_ID) FROM Inscripciones WHERE Inscripcion_ID > @Ins5;
SELECT @Ins7 = MIN(Inscripcion_ID) FROM Inscripciones WHERE Inscripcion_ID > @Ins6;
SELECT @Ins8 = MIN(Inscripcion_ID) FROM Inscripciones WHERE Inscripcion_ID > @Ins7;
SELECT @Ins9 = MIN(Inscripcion_ID) FROM Inscripciones WHERE Inscripcion_ID > @Ins8;
SELECT @Ins10 = MIN(Inscripcion_ID) FROM Inscripciones WHERE Inscripcion_ID > @Ins9;

EXEC Registrar_Evaluacion @Ins1, 9.5, 'Excelente dominio del tema, muy participativo.';
EXEC Registrar_Evaluacion @Ins2, 8.0, 'Buen desempeno, entrega a tiempo.';
EXEC Registrar_Evaluacion @Ins3, 7.5, 'Cumple con los requisitos minimos.';
EXEC Registrar_Evaluacion @Ins4, 9.0, 'Muy buen trabajo en equipo.';
EXEC Registrar_Evaluacion @Ins5, 6.5, 'Requiere mejorar en practicas.';
EXEC Registrar_Evaluacion @Ins6, 10.0, 'Excelente, destacado en el curso.';
EXEC Registrar_Evaluacion @Ins7, 8.5, 'Buen avance, participacion activa.';
EXEC Registrar_Evaluacion @Ins8, 7.0, 'Presenta areas de oportunidad.';
EXEC Registrar_Evaluacion @Ins9, 9.2, 'Muy buen desempeno academico.';
EXEC Registrar_Evaluacion @Ins10, 8.8, 'Buen trabajo final entregado.';
GO


-- 16 TÉCNICAS AVANZADAS (CASE, RANKING, PIVOT, JOIN COMPLEJO)

--CASE 
SELECT

    e.Nombre + ' ' + e.Apellidos AS Estudiante,
    c.Nombre_Curso,
    ev.Calificacion,
    CASE 
        WHEN ev.Calificacion >= 9 THEN 'Excelente'
        WHEN ev.Calificacion >= 7 THEN 'Bueno'
        WHEN ev.Calificacion >= 6 THEN 'Suficiente'
        WHEN ev.Calificacion IS NULL THEN 'Sin evaluar'
        ELSE 'Reprobado'
    END AS Desempeno
FROM Evaluaciones ev

INNER JOIN Inscripciones i ON ev.Inscripcion_ID = i.Inscripcion_ID

INNER JOIN Estudiantes e ON i.Estudiante_ID = e.Estudiante_ID

INNER JOIN Grupos g ON i.Grupo_ID = g.Grupo_ID

INNER JOIN Cursos c ON g.Curso_ID = c.Curso_ID

ORDER BY ev.Calificacion DESC;
GO



--RANKING - Cursos mas demandados
SELECT

    c.Nombre_Curso,
    COUNT(i.Inscripcion_ID) AS Total_Inscripciones,
    RANK() OVER (ORDER BY COUNT(i.Inscripcion_ID) DESC) AS Ranking
FROM Cursos c

INNER JOIN Grupos g ON c.Curso_ID = g.Curso_ID

INNER JOIN Inscripciones i ON g.Grupo_ID = i.Grupo_ID

GROUP BY c.Curso_ID, c.Nombre_Curso

ORDER BY Ranking;
GO



--PIVOT

IF OBJECT_ID('Inscripciones_Pivot', 'U') IS NOT NULL

    DROP TABLE Inscripciones_Pivot;
GO

-- Crear tabla para almacenar el PIVOT

CREATE TABLE Inscripciones_Pivot(

    Anio INT,
    Enero INT DEFAULT 0, 
    Febrero INT DEFAULT 0, 
    Marzo INT DEFAULT 0, 
    Abril INT DEFAULT 0, 
    Mayo INT DEFAULT 0, 
    Junio INT DEFAULT 0,
    Julio INT DEFAULT 0, 
    Agosto INT DEFAULT 0, 
    Septiembre INT DEFAULT 0, 
    Octubre INT DEFAULT 0, 
    Noviembre INT DEFAULT 0, 
    Diciembre INT DEFAULT 0
);
GO

-- Insertar datos con PIVOT 

INSERT INTO Inscripciones_Pivot (Anio, Enero, Febrero, Marzo, Abril, Mayo, Junio,

Julio, Agosto, Septiembre, Octubre, Noviembre, Diciembre)

SELECT

    Anio,
    ISNULL([1], 0) AS Enero,
    ISNULL([2], 0) AS Febrero,
    ISNULL([3], 0) AS Marzo,
    ISNULL([4], 0) AS Abril,
    ISNULL([5], 0) AS Mayo,
    ISNULL([6], 0) AS Junio,
    ISNULL([7], 0) AS Julio,
    ISNULL([8], 0) AS Agosto,
    ISNULL([9], 0) AS Septiembre,
    ISNULL([10], 0) AS Octubre,
    ISNULL([11], 0) AS Noviembre,
    ISNULL([12], 0) AS Diciembre
FROM (

    SELECT 
        YEAR(Fecha_Inscripcion) AS Anio,
        MONTH(Fecha_Inscripcion) AS Mes,
        Inscripcion_ID
    FROM Inscripciones
) AS Datos
PIVOT (

    COUNT(Inscripcion_ID)
    FOR Mes IN ([1],[2],[3],[4],[5],[6],[7],[8],[9],[10],[11],[12])
) AS PivotTable;
GO

-- Ver resultado del PIVOT

SELECT * FROM Inscripciones_Pivot;
GO



--  JOIN COMPLEJO 


SELECT

    u.email AS Correo_Estudiante,
    e.Nombre + ' ' + e.Apellidos AS Estudiante,
    c.Nombre_Curso,
    inst.Nombre + ' ' + inst.Apellidos AS Instructor,   
    ins.Fecha_Inscripcion,
    ins.Estado AS Estado_Inscripcion,
    ev.Calificacion,
    CASE 
        WHEN ev.Calificacion >= 7 THEN 'Aprobado'
        WHEN ev.Calificacion IS NULL THEN 'Pendiente'
        ELSE 'No aprobado'
    END AS Resultado,
    p.Monto AS Monto_Pagado,
    p.Metodo_Pago,
    p.Fecha_Pago
FROM Inscripciones ins

INNER JOIN Estudiantes e ON ins.Estudiante_ID = e.Estudiante_ID

INNER JOIN Usuarios u ON e.Usuario_ID = u.Usuario_ID

INNER JOIN Grupos g ON ins.Grupo_ID = g.Grupo_ID

INNER JOIN Cursos c ON g.Curso_ID = c.Curso_ID

INNER JOIN Instructores inst ON g.Instructor_ID = inst.Instructor_ID

LEFT JOIN Evaluaciones ev ON ins.Inscripcion_ID = ev.Inscripcion_ID

LEFT JOIN Pagos p ON ins.Inscripcion_ID = p.Inscripcion_ID

ORDER BY ins.Fecha_Inscripcion DESC;
GO



-- FRAGMENTACIÓN HORIZONTAL 

-- 1.1 Estudiantes por Tipo_Documento
SELECT * INTO Estudiantes_INE FROM Estudiantes WHERE 1=0;
SELECT * INTO Estudiantes_Pasaporte FROM Estudiantes WHERE 1=0;


SET IDENTITY_INSERT Estudiantes_INE ON;
INSERT INTO Estudiantes_INE (Estudiante_ID, Usuario_ID, Nombre, Apellidos, Direccion, Telefono, Tipo_Documento, Numero_Documento, Fecha_Registro)
SELECT Estudiante_ID, Usuario_ID, Nombre, Apellidos, Direccion, Telefono, Tipo_Documento, Numero_Documento, Fecha_Registro
FROM Estudiantes WHERE Tipo_Documento = 'INE';
SET IDENTITY_INSERT Estudiantes_INE OFF;

SET IDENTITY_INSERT Estudiantes_Pasaporte ON;
INSERT INTO Estudiantes_Pasaporte (Estudiante_ID, Usuario_ID, Nombre, Apellidos, Direccion, Telefono, Tipo_Documento, Numero_Documento, Fecha_Registro)
SELECT Estudiante_ID, Usuario_ID, Nombre, Apellidos, Direccion, Telefono, Tipo_Documento, Numero_Documento, Fecha_Registro
FROM Estudiantes WHERE Tipo_Documento = 'Pasaporte';
SET IDENTITY_INSERT Estudiantes_Pasaporte OFF;

PRINT '=== Fragmentación Horizontal: Estudiantes_INE y Estudiantes_Pasaporte creadas ===';

-- 1.2 Instructores por Especialidad
SELECT * INTO Instructores_TI FROM Instructores WHERE 1=0;
SELECT * INTO Instructores_Redes FROM Instructores WHERE 1=0;
SELECT * INTO Instructores_Otra FROM Instructores WHERE 1=0;

SET IDENTITY_INSERT Instructores_TI ON;
INSERT INTO Instructores_TI (Instructor_ID, Usuario_ID, Nombre, Apellidos, Especialidad, Cedula_Profesional, Estado)
SELECT Instructor_ID, Usuario_ID, Nombre, Apellidos, Especialidad, Cedula_Profesional, Estado
FROM Instructores WHERE Especialidad IN ('Criptografia', 'Programacion', 'Frontend', 'DevOps', 'Arquitectura de Software', 'Metodologias Agiles');
SET IDENTITY_INSERT Instructores_TI OFF;

SET IDENTITY_INSERT Instructores_Redes ON;
INSERT INTO Instructores_Redes (Instructor_ID, Usuario_ID, Nombre, Apellidos, Especialidad, Cedula_Profesional, Estado)
SELECT Instructor_ID, Usuario_ID, Nombre, Apellidos, Especialidad, Cedula_Profesional, Estado
FROM Instructores WHERE Especialidad IN ('Redes', 'Ciberseguridad');
SET IDENTITY_INSERT Instructores_Redes OFF;

SET IDENTITY_INSERT Instructores_Otra ON;
INSERT INTO Instructores_Otra (Instructor_ID, Usuario_ID, Nombre, Apellidos, Especialidad, Cedula_Profesional, Estado)
SELECT Instructor_ID, Usuario_ID, Nombre, Apellidos, Especialidad, Cedula_Profesional, Estado
FROM Instructores WHERE Especialidad NOT IN ('Criptografia', 'Programacion', 'Frontend', 'DevOps', 'Arquitectura de Software', 'Metodologias Agiles', 'Redes', 'Ciberseguridad') OR Especialidad IS NULL;
SET IDENTITY_INSERT Instructores_Otra OFF;

PRINT '=== Fragmentación Horizontal: Instructores_TI, Instructores_Redes, Instructores_Otra creadas ===';

-- 1.3 Cursos por Categoria
SELECT * INTO Cursos_Programacion FROM Cursos WHERE 1=0;
SELECT * INTO Cursos_Redes FROM Cursos WHERE 1=0;
SELECT * INTO Cursos_Ciberseguridad FROM Cursos WHERE 1=0;
SELECT * INTO Cursos_Otra FROM Cursos WHERE 1=0;

SET IDENTITY_INSERT Cursos_Programacion ON;
INSERT INTO Cursos_Programacion (Curso_ID, Nombre_Curso, Categoria, Duracion_Horas, Costo, Estado)
SELECT Curso_ID, Nombre_Curso, Categoria, Duracion_Horas, Costo, Estado
FROM Cursos WHERE Categoria IN ('Programacion', 'Frontend', 'DevOps', 'Arquitectura de Software', 'Metodologias Agiles');
SET IDENTITY_INSERT Cursos_Programacion OFF;

SET IDENTITY_INSERT Cursos_Redes ON;
INSERT INTO Cursos_Redes (Curso_ID, Nombre_Curso, Categoria, Duracion_Horas, Costo, Estado)
SELECT Curso_ID, Nombre_Curso, Categoria, Duracion_Horas, Costo, Estado
FROM Cursos WHERE Categoria = 'Redes';
SET IDENTITY_INSERT Cursos_Redes OFF;

SET IDENTITY_INSERT Cursos_Ciberseguridad ON;
INSERT INTO Cursos_Ciberseguridad (Curso_ID, Nombre_Curso, Categoria, Duracion_Horas, Costo, Estado)
SELECT Curso_ID, Nombre_Curso, Categoria, Duracion_Horas, Costo, Estado
FROM Cursos WHERE Categoria IN ('Ciberseguridad');
SET IDENTITY_INSERT Cursos_Ciberseguridad OFF;

SET IDENTITY_INSERT Cursos_Otra ON;
INSERT INTO Cursos_Otra (Curso_ID, Nombre_Curso, Categoria, Duracion_Horas, Costo, Estado)
SELECT Curso_ID, Nombre_Curso, Categoria, Duracion_Horas, Costo, Estado
FROM Cursos WHERE Categoria NOT IN ('Programacion', 'Frontend', 'DevOps', 'Arquitectura de Software', 'Metodologias Agiles', 'Redes', 'Ciberseguridad') OR Categoria IS NULL;
SET IDENTITY_INSERT Cursos_Otra OFF;

PRINT '=== Fragmentación Horizontal: Cursos_Programacion, Cursos_Redes, Cursos_Ciberseguridad, Cursos_Otra creadas ===';

-- 1.4 Grupos por Cupo_Disponible
SELECT * INTO Grupos_Disponibles FROM Grupos WHERE 1=0;
SELECT * INTO Grupos_Llenos FROM Grupos WHERE 1=0;

-- Grupos no tienen IDENTITY, se pueden insertar directamente
INSERT INTO Grupos_Disponibles SELECT * FROM Grupos WHERE Cupo_Disponible > 0;
INSERT INTO Grupos_Llenos SELECT * FROM Grupos WHERE Cupo_Disponible = 0;

PRINT '=== Fragmentación Horizontal: Grupos_Disponibles y Grupos_Llenos creadas ===';


-- FRAGMENTACIÓN VERTICAL 


-- 2.1 Estudiantes: separar datos sensibles
SELECT Estudiante_ID, Nombre, Apellidos, Direccion, Telefono, Fecha_Registro
INTO Estudiantes_Normales
FROM Estudiantes;

SELECT Estudiante_ID, Tipo_Documento, Numero_Documento
INTO Estudiantes_Sensibles
FROM Estudiantes;

PRINT '=== Fragmentación Vertical: Estudiantes_Normales y Estudiantes_Sensibles creadas ===';

-- 2.2 Instructores: separar cédula cifrada
SELECT Instructor_ID, Nombre, Apellidos, Especialidad, Estado
INTO Instructores_Normales
FROM Instructores;

SELECT Instructor_ID, Cedula_Profesional
INTO Instructores_Cedulas
FROM Instructores;

PRINT '=== Fragmentación Vertical: Instructores_Normales y Instructores_Cedulas creadas ===';





-- 17 . PRUEBAS DE TABLAS

--Tablas originales

SELECT* FROM Estudiantes
SELECT* FROM Instructores
SELECT* FROM Cursos
SELECT* FROM Grupos
SELECT* FROM Inscripciones
SELECT* FROM Evaluaciones
SELECT* FROM Pagos

--Verificacion de Auditorias


SELECT* FROM Estudiantes

UPDATE Estudiantes SET Nombre = 'Gregorio'

DELETE FROM Estudiantes WHERE Apellidos = 'Moctezuma'


PRINT '--- Auditoria Estudiantes ---';
SELECT TOP 5 * FROM Auditoria_Estudiantes ORDER BY Auditoria_Est_ID DESC;

----------------------------------------------------------------------------------------

SELECT* FROM Instructores

UPDATE Instructores SET Nombre = 'Ivann'

DELETE FROM Instructores WHERE Apellidos = 'Moctezuma'



PRINT '--- Auditoria Instructores ---';
SELECT TOP 5 * FROM Auditoria_Instructores ORDER BY Auditoria_Ins_Inst_ID DESC;

------------------------------------------------------------------------------

SELECT* FROM Cursos

UPDATE Cursos SET Categoria= 'Matematicas'

DELETE FROM Cursos WHERE Nombre_Curso = 'Matematicas'


PRINT '--- Auditoria Cursos ---';
SELECT TOP 5 * FROM Auditoria_Cursos ORDER BY Auditoria_Cur_ID DESC;



------------------------------------------------------------------------------

SELECT* FROM Grupos

UPDATE Grupos SET Cupo_Maximo = 15

DELETE FROM Grupos WHERE Grupo_ID = 'GRUPO-10'


PRINT '--- Auditoria Grupos ---';
SELECT TOP 5 * FROM Auditoria_Grupos ORDER BY Auditoria_Gru_ID DESC;


----------------------------------------------------------------------------------------

SELECT * FROM Inscripciones;

UPDATE Inscripciones SET Estado = 'Cancelada' WHERE Inscripcion_ID = 1001;


DELETE FROM Inscripciones WHERE Inscripcion_ID = 1001;

PRINT '--- Auditoria Inscripciones ---';
SELECT TOP 5 * FROM Auditoria_Inscripciones ORDER BY Auditoria_Ins_ID DESC;

--------------------------------------------------------------------------------------------------


SELECT * FROM Evaluaciones;


UPDATE Evaluaciones SET Calificacion = 9.0 WHERE Evaluacion_ID = 1;


DELETE FROM Evaluaciones WHERE Evaluacion_ID = 5;


PRINT '--- Auditoria Evaluaciones ---';
SELECT TOP 5 * FROM Auditoria_Evaluaciones ORDER BY Auditoria_Eva_ID DESC;



----------------------------------------------------------------------------------------------


PRINT '--- Auditoria Pagos ---';
SELECT TOP 5 * FROM Auditoria_Pagos ORDER BY Auditoria_Pago_ID DESC;
GO
-------------------------------------------------------------------------------------------------

-- Ver todos los triggers de la base de datos
SELECT 
    t.name AS Nombre_Trigger,
    OBJECT_NAME(t.parent_id) AS Tabla,
    t.type_desc AS Tipo,
    t.is_disabled AS Deshabilitado,
    t.create_date AS Fecha_Creacion,
    t.modify_date AS Ultima_Modificacion
FROM sys.triggers t
WHERE t.parent_id > 0
ORDER BY Tabla, Nombre_Trigger;
GO

-- VERIFICACIÓN DE FRAGMENTACIÓN

PRINT '--- Fragmentación Horizontal ---';
SELECT 'Estudiantes_INE' as Tabla, COUNT(*) as Registros FROM Estudiantes_INE
UNION ALL SELECT 'Estudiantes_Pasaporte', COUNT(*) FROM Estudiantes_Pasaporte;

SELECT 'Instructores_TI' as Tabla, COUNT(*) as Registros FROM Instructores_TI
UNION ALL SELECT 'Instructores_Redes', COUNT(*) FROM Instructores_Redes
UNION ALL SELECT 'Instructores_Otra', COUNT(*) FROM Instructores_Otra;

SELECT 'Cursos_Programacion' as Tabla, COUNT(*) as Registros FROM Cursos_Programacion
UNION ALL SELECT 'Cursos_Redes', COUNT(*) FROM Cursos_Redes
UNION ALL SELECT 'Cursos_Ciberseguridad', COUNT(*) FROM Cursos_Ciberseguridad
UNION ALL SELECT 'Cursos_Otra', COUNT(*) FROM Cursos_Otra;

SELECT 'Grupos_Disponibles' as Tabla, COUNT(*) as Registros FROM Grupos_Disponibles
UNION ALL SELECT 'Grupos_Llenos', COUNT(*) FROM Grupos_Llenos;

PRINT '--- Fragmentación Vertical ---';
SELECT 'Estudiantes_Normales' as Tabla, COUNT(*) as Registros FROM Estudiantes_Normales
UNION ALL SELECT 'Estudiantes_Sensibles', COUNT(*) FROM Estudiantes_Sensibles;

SELECT 'Instructores_Normales' as Tabla, COUNT(*) as Registros FROM Instructores_Normales
UNION ALL SELECT 'Instructores_Cedulas', COUNT(*) FROM Instructores_Cedulas;
GO


-- 15. PRUEBAS DE CIFRADO/DESCIFRADO


-- Documentos de estudiantes
PRINT '=== Documentos de Estudiantes ===';
OPEN SYMMETRIC KEY ClaveEducacion DECRYPTION BY CERTIFICATE CertificadoEducacion;
SELECT 
    e.Nombre, e.Apellidos,
    e.Numero_Documento AS Documento_Cifrado,
    CONVERT(VARCHAR(50), DecryptByKey(e.Numero_Documento)) AS Documento_Descifrado
FROM Estudiantes e;
CLOSE SYMMETRIC KEY ClaveEducacion;
GO


-- Cédulas de instructores
PRINT '=== Cédulas de Instructores ===';
OPEN SYMMETRIC KEY ClaveEducacion DECRYPTION BY CERTIFICATE CertificadoEducacion;
SELECT 
    i.Nombre, i.Apellidos,
    i.Cedula_Profesional AS Cedula_Cifrada,
    CONVERT(VARCHAR(50), DecryptByKey(i.Cedula_Profesional)) AS Cedula_Descifrada
FROM Instructores i;
CLOSE SYMMETRIC KEY ClaveEducacion;
GO

-- Contraseñas de usuarios
PRINT '=== Contraseñas de Usuarios ===';
OPEN SYMMETRIC KEY ClaveEducacion DECRYPTION BY CERTIFICATE CertificadoEducacion;
SELECT 
    u.email,
    u.Contrasena AS Contrasena_Cifrada,
    CONVERT(VARCHAR(50), DecryptByKey(u.Contrasena)) AS Contrasena_Descifrada
FROM Usuarios u;
CLOSE SYMMETRIC KEY ClaveEducacion;
GO

-- Referencias de pagos
PRINT '=== Referencias de Pagos ===';
OPEN SYMMETRIC KEY ClaveEducacion DECRYPTION BY CERTIFICATE CertificadoEducacion;
SELECT 
    p.Pagos_ID, p.Monto,
    p.Referencia_Pago AS Referencia_Cifrada,
    CONVERT(VARCHAR(100), DecryptByKey(p.Referencia_Pago)) AS Referencia_Descifrada
FROM Pagos p;
CLOSE SYMMETRIC KEY ClaveEducacion;
GO



--16.Verificar Bitacora de error

SELECT * FROM Bitacora_Errores ORDER BY Error_Log_ID DESC;
GO
--Forzar Error
EXEC Registrar_Estudiante 'est1@edu.com', '123456', 'Prueba', 'Error', 'Calle 1', '123', 'INE', 'DOC-999';

-----------------------------------------------------------------------------------------------


OPEN SYMMETRIC KEY ClaveEducacion DECRYPTION BY CERTIFICATE CertificadoEducacion;

INSERT INTO Usuarios (Rol_ID, email, Contrasena, Estado)
VALUES (1, 'admin@edu.com', EncryptByKey(Key_GUID('ClaveEducacion'), 'Admin2026!'), 'Activo');

CLOSE SYMMETRIC KEY ClaveEducacion;
GO


SELECT * FROM auth_user WHERE email = 'admin@edu.com';
SELECT * FROM Usuarios WHERE email = 'admin@edu.com';



INSERT INTO DetallesPagos (Pago_ID, Concepto, Cantidad, Precio_Unitario, Subtotal)
SELECT 
    p.Pagos_ID,
    'Inscripción a curso' AS Concepto,
    1 AS Cantidad,
    p.Monto AS Precio_Unitario,
    p.Monto AS Subtotal
FROM Pagos p
WHERE NOT EXISTS (
    SELECT 1 FROM DetallesPagos d WHERE d.Pago_ID = p.Pagos_ID
);