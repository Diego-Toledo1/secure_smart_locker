import sys
import os
import pymysql
import logging
import hashlib # para hashear el passowrd admin

# Configuración básica de logs
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Lectura de variables de entorno
try:
    rds_host = os.environ['RDS_HOST']
    name = os.environ['RDS_USER']
    password = os.environ['RDS_PASSWORD']
    db_name = os.environ['RDS_DB_NAME']
except KeyError as e:
    logger.error(f"Error: Falta la variable de entorno {e}")
    sys.exit(1)

def hash_password(password):
    """Genera hash compatible con el sistema de Auth"""
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return f"{salt}${hashed}"

def create_admin_user(conn):
    """Crea un usuario administrador por defecto si no existe"""
    admin_email = "admin@utez.edu.mx"
    admin_pass = "AdminSecret123" # Contraseña por defecto
    admin_name = "Super Administrador"

    with conn.cursor() as cur:
        # Verificar si ya existe
        cur.execute("SELECT id FROM users WHERE email = %s", (admin_email,))
        if cur.fetchone():
            logger.info("El Admin ya existe. No se hace nada.")
            return

        # Crear Admin
        logger.info("Creando usuario Admin por defecto...")
        pwd_hash = hash_password(admin_pass)
        
        sql = """
            INSERT INTO users (email, password_hash, name, role, created_at) 
            VALUES (%s, %s, %s, 'admin', NOW())
        """
        cur.execute(sql, (admin_email, pwd_hash, admin_name))
        conn.commit()
        logger.info("Usuario Admin creado exitosamente.")

def lambda_handler(event, context):
    conn = None
    try:
        logger.info(f"Conectando a {rds_host}...")
        conn = pymysql.connect(
            host=rds_host, user=name, passwd=password, connect_timeout=10
        )
        logger.info("Conexión exitosa.")
        
        # 1. Ejecutar Schema SQL (Tablas)
        with open('rds_schema.sql', 'r') as file:
            sql_script = file.read()
            
        statements = sql_script.split(';')
        with conn.cursor() as cur:
            cur.execute(f"USE {db_name}") 
            for statement in statements:
                if statement.strip():
                    cur.execute(statement)
            conn.commit()
        
        # 2. Inyectar Admin User (Python Logic)
        # Nos reconectamos asegurando la DB seleccionada
        conn.select_db(db_name)
        create_admin_user(conn)

        return {
            'statusCode': 200,
            'body': "Base de datos actualizada y Admin creado (admin@utez.edu.mx)."
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Error: {str(e)}"
        }
    finally:
        if conn: conn.close()