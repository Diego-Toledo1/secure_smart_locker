import json
import os
import logging
import random
import hashlib
from datetime import datetime, timedelta
import db_utils # Usaremos el mismo helper

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    path = event.get('path', '') or event.get('rawPath', '')
    http_method = event.get('httpMethod', '') or event.get('requestContext', {}).get('http', {}).get('method')
    
    logger.info(f"Request: {http_method} {path}")

    if http_method == 'OPTIONS':
        return db_utils.format_response(200, {})

    # Router básico
    if 'available' in path and http_method == 'GET':
        return get_available_lockers()
    elif 'assign' in path and http_method == 'POST':
        return assign_locker(event)
    elif 'my-locker' in path: # Puede ser GET (info) o POST (acciones)
        if http_method == 'GET':
            return get_my_locker(event)
    
    return db_utils.format_response(404, {'message': 'Ruta lockers no encontrada'})

def generate_otp():
    """Genera OTP de 6 dígitos, su hash y su salt"""
    otp = str(random.randint(100000, 999999))
    salt = os.urandom(16).hex()
    otp_hash = hashlib.sha256((otp + salt).encode('utf-8')).hexdigest()
    return otp, salt, otp_hash

def get_available_lockers():
    conn = db_utils.get_db_connection()
    try:
        with conn.cursor() as cur:
            # Solo traemos ID, Codigo y Status
            cur.execute("SELECT id, code, status FROM lockers WHERE status = 'available'")
            lockers = cur.fetchall()
        return db_utils.format_response(200, lockers)
    except Exception as e:
        logger.error(str(e))
        return db_utils.format_response(500, {'error': str(e)})
    finally:
        conn.close()

def assign_locker(event):
    """
    Asigna un locker al usuario.
    Body esperado: { "user_id": 1, "locker_id": 5, "days": 1, "color": "#FF0000" }
    """
    try:
        body = json.loads(event.get('body', '{}'))
        user_id = body.get('user_id')
        locker_id = body.get('locker_id')
        days = int(body.get('days', 1))
        color = body.get('color', '#000000')

        if not user_id or not locker_id:
            return db_utils.format_response(400, {'message': 'Faltan user_id o locker_id'})

        conn = db_utils.get_db_connection()
        with conn.cursor() as cur:
            # 1. Validar si el usuario YA tiene un locker activo
            cur.execute("SELECT id FROM lockers WHERE current_user_id = %s", (user_id,))
            if cur.fetchone():
                return db_utils.format_response(409, {'message': 'El usuario ya tiene un locker asignado'})

            # 2. Validar si el locker deseado está libre
            cur.execute("SELECT status FROM lockers WHERE id = %s", (locker_id,))
            locker = cur.fetchone()
            if not locker or locker['status'] != 'available':
                return db_utils.format_response(409, {'message': 'El locker no esta disponible'})

            # 3. Asignar: Generar primer OTP y calcular fecha
            otp_plain, salt, otp_hash = generate_otp()
            
            # Query de actualización
            sql = """
                UPDATE lockers 
                SET status='occupied', 
                    current_user_id=%s, 
                    assigned_at=NOW(), 
                    expires_at=DATE_ADD(NOW(), INTERVAL %s DAY),
                    current_otp_hash=%s,
                    otp_salt=%s,
                    otp_valid_until=DATE_ADD(NOW(), INTERVAL 15 MINUTE),
                    color_hex=%s
                WHERE id=%s
            """
            cur.execute(sql, (user_id, days, otp_hash, salt, color, locker_id))
            conn.commit()

            # Respondemos con el OTP plano (solo esta vez) para que el usuario lo vea de inmediato
            return db_utils.format_response(200, {
                'message': 'Locker asignado correctamente',
                'initial_otp': otp_plain
            })

    except Exception as e:
        logger.error(str(e))
        return db_utils.format_response(500, {'error': str(e)})
    finally:
        if 'conn' in locals(): conn.close()

def get_my_locker(event):
    """
    Obtiene el locker del usuario basado en user_id (query param por ahora)
    Ejemplo: GET /lockers/my-locker?user_id=1
    """
    try:
        # Obtener user_id de query parameters
        params = event.get('queryStringParameters', {}) or {}
        user_id = params.get('user_id')

        if not user_id:
            return db_utils.format_response(400, {'message': 'Falta user_id en query params'})

        conn = db_utils.get_db_connection()
        with conn.cursor() as cur:
            sql = """
                SELECT id, code, status, expires_at, color_hex 
                FROM lockers 
                WHERE current_user_id = %s
            """
            cur.execute(sql, (user_id,))
            locker = cur.fetchone()

            if not locker:
                return db_utils.format_response(404, {'message': 'Usuario sin locker asignado'})
            
            return db_utils.format_response(200, locker)

    except Exception as e:
        logger.error(str(e))
        return db_utils.format_response(500, {'error': str(e)})
    finally:
        if 'conn' in locals(): conn.close()