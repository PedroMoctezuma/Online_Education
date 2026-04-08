from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.db import connection
from django.conf import settings
from .models import Usuarios
import pyodbc


def set_session_context(usuario_id):
    """Establece el usuario_id en el contexto de sesión de SQL Server usando la conexión de Django"""
    try:
        with connection.cursor() as cursor:
            # Usar parámetro con formato correcto para SQL Server
            cursor.execute("EXEC sp_set_session_context @key = N'usuario_id', @value = %s", [usuario_id])
    except Exception as e:
        print(f"Error al establecer contexto de sesión: {e}")


class SQLLoginBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        if not username or not password:
            return None
            
        try:
            # Obtener el usuario de la base de datos
            usuario = Usuarios.objects.get(email=username)
            
            if usuario.estado != 'Activo':
                return None
            
            # Conectar a SQL Server para descifrar la contraseña
            conn = None
            cursor = None
            try:
                # Usar autenticación de Windows (Trusted_Connection)
                # Si necesitas usar usuario/contraseña específicos, cambia la cadena de conexión
                conn = pyodbc.connect(
                    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                    f"SERVER={settings.DATABASES['default']['HOST']};"
                    f"DATABASE={settings.DATABASES['default']['NAME']};"
                    f"Trusted_Connection=yes;"
                    f"TrustServerCertificate=yes;"
                )
                cursor = conn.cursor()
                
                # Descifrar la contraseña del usuario
                cursor.execute("""
                    OPEN SYMMETRIC KEY ClaveEducacion DECRYPTION BY CERTIFICATE CertificadoEducacion;
                    SELECT CONVERT(VARCHAR(100), DecryptByKey(Contrasena)) 
                    FROM Usuarios WHERE email = ? AND Estado = 'Activo';
                    CLOSE SYMMETRIC KEY ClaveEducacion;
                """, username)
                
                row = cursor.fetchone()
                
                if row and row[0] == password:
                    # Establecer el contexto de sesión para toda la sesión del usuario
                    if request:
                        request.session['rol_id'] = usuario.rol.rol_id
                        request.session['usuario_id'] = usuario.usuario_id
                        request.session['user_email'] = usuario.email
                        
                        # IMPORTANTE: Establecer el contexto de sesión en SQL Server
                        # Esto asegura que durante toda la sesión, el usuario_id esté disponible
                        set_session_context(usuario.usuario_id)
                    
                    # Crear o obtener el usuario de Django
                    try:
                        user = User.objects.get(username=username)
                        # Actualizar información por si acaso
                        user.email = username
                        user.save()
                    except User.DoesNotExist:
                        # Crear usuario de Django según el rol
                        if usuario.rol.rol_id == 1:  # Administrador
                            user = User.objects.create_user(
                                username=username, 
                                email=username,
                                password=None  # No guardar contraseña en Django
                            )
                            user.is_active = True
                            user.is_superuser = True
                            user.is_staff = True
                        elif usuario.rol.rol_id == 2:  # Instructor
                            user = User.objects.create_user(
                                username=username,
                                email=username,
                                password=None
                            )
                            user.is_active = True
                            user.is_staff = True  # Instructores pueden acceder al admin?
                        else:  # Estudiante
                            user = User.objects.create_user(
                                username=username,
                                email=username,
                                password=None
                            )
                            user.is_active = True
                        user.save()
                    
                    return user
                    
            except pyodbc.Error as e:
                print(f"Error de conexión a SQL Server: {e}")
                return None
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
                    
        except Usuarios.DoesNotExist:
            return None
        except Exception as e:
            print(f"Error inesperado en autenticación: {e}")
            return None
            
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None