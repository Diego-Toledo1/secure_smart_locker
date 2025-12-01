import json
import hashlib
import os
import logging
# Importamos la utilidad que acabamos de crear (estará en la misma carpeta en el ZIP)
import db_utils 

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Router principal para /auth/register y /auth/login
    """
    # Detectar path y método desde API Gateway
    path = event.get('path', '') or event.get('rawPath', '')
    http_method = event.get('httpMethod', '') or event.get('requestContext', {}).get('http', {}).get('method')
    
    logger.info(f"Solicitud recibida: {http_method} {path}")

    if http_method == 'OPTIONS':
        return db_utils.format_response(200, {})

    if 'register' in path and http_method == 'POST':
        return register(event)
    elif 'login' in path and http_method == 'POST':
        return login(event)
    else:
        return db_utils.format_response(404, {'message': 'Ruta no encontrada'})

def hash_password(password):
    """Genera un salt y devuelve salt$hash"""
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return f"{salt}${hashed}"

def verify_password(stored_password, input_password):
    """Verifica salt$hash contra el input"""
    try:
        salt, hashed = stored_password.split('$')
        check_hash = hashlib.sha256((input_password + salt).encode('utf-8')).hexdigest()
        return check_hash == hashed
    except ValueError:
        return False

def register(event):
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email')
        password = body.get('password')
        name = body.get('name')

        if not email or not password or not name:
            return db_utils.format_response(400, {'message': 'Faltan datos (email, password, name)'})

        conn = db_utils.get_db_connection()
        with conn.cursor() as cur:
            # Verificar duplicados
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                return db_utils.format_response(409, {'message': 'El usuario ya existe'})

            # Hash + Insertar
            pwd_hash = hash_password(password)
            sql = "INSERT INTO users (email, password_hash, name, role, created_at) VALUES (%s, %s, %s, 'user', NOW())"
            cur.execute(sql, (email, pwd_hash, name))
            conn.commit()
            
        return db_utils.format_response(201, {'message': 'Usuario registrado exitosamente'})
    except Exception as e:
        logger.error(e)
        return db_utils.format_response(500, {'error': str(e)})
    finally:
        if 'conn' in locals(): conn.close()

def login(event):
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email')
        password = body.get('password')

        conn = db_utils.get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, role, password_hash FROM users WHERE email = %s", (email,))
            user = cur.fetchone()

            if user and verify_password(user['password_hash'], password):
                # Login exitoso
                return db_utils.format_response(200, {
                    'message': 'Login exitoso',
                    'user': {
                        'id': user['id'],
                        'name': user['name'],
                        'email': email,
                        'role': user['role']
                    },
                    'token': f"mock-jwt-{user['id']}-{os.urandom(4).hex()}" # Placeholder para JWT real
                })
            else:
                return db_utils.format_response(401, {'message': 'Credenciales inválidas'})
    except Exception as e:
        logger.error(e)
        return db_utils.format_response(500, {'error': str(e)})
    finally:
        if 'conn' in locals(): conn.close()