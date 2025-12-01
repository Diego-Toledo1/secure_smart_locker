import json
import logging
import db_utils # Usaremos el helper compartido

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    path = event.get('path', '') or event.get('rawPath', '')
    http_method = event.get('httpMethod', '') or event.get('requestContext', {}).get('http', {}).get('method')
    
    logger.info(f"Admin Request: {http_method} {path}")

    if http_method == 'OPTIONS':
        return db_utils.format_response(200, {})

    # Router de Admin
    if 'force-release' in path and http_method == 'DELETE':
        return force_release_locker(path)
    elif '/admin/lockers' in path and http_method == 'GET':
        # Importante: verificar que sea la ruta base y no una subruta no manejada
        return get_all_lockers()
    
    return db_utils.format_response(404, {'message': 'Ruta admin no encontrada'})

def get_all_lockers():
    """Trae TODOS los lockers con datos del usuario si está ocupado"""
    conn = db_utils.get_db_connection()
    try:
        with conn.cursor() as cur:
            # JOIN para traer nombre y email del usuario
            sql = """
                SELECT 
                    l.id, l.code, l.status, l.expires_at, l.color_hex,
                    u.name as user_name, u.email as user_email
                FROM lockers l
                LEFT JOIN users u ON l.current_user_id = u.id
                ORDER BY l.code ASC
            """
            cur.execute(sql)
            lockers = cur.fetchall()
        return db_utils.format_response(200, lockers)
    except Exception as e:
        logger.error(str(e))
        return db_utils.format_response(500, {'error': str(e)})
    finally:
        conn.close()

def force_release_locker(path):
    """
    Extrae el ID de la URL y fuerza la liberación.
    Ruta esperada: /admin/lockers/{id}/force-release
    """
    try:
        # Extraer ID de la ruta (hack rápido, idealmente usariamos pathParameters)
        # Asumiendo formato .../lockers/123/force-release
        parts = path.split('/')
        if 'force-release' not in parts:
             return db_utils.format_response(400, {'message': 'URL malformada'})
        
        # El ID debería estar antes de 'force-release'
        idx = parts.index('force-release')
        locker_id = parts[idx - 1]

        if not locker_id.isdigit():
            return db_utils.format_response(400, {'message': 'ID de locker inválido'})

        conn = db_utils.get_db_connection()
        with conn.cursor() as cur:
            # Resetear el locker a disponible
            sql = """
                UPDATE lockers 
                SET status='available', 
                    current_user_id=NULL, 
                    assigned_at=NULL, 
                    expires_at=NULL,
                    current_otp_hash=NULL,
                    otp_salt=NULL,
                    otp_valid_until=NULL,
                    color_hex=NULL
                WHERE id=%s
            """
            cur.execute(sql, (locker_id,))
            conn.commit()
            
        return db_utils.format_response(200, {'message': f'Locker {locker_id} liberado forzosamente'})

    except Exception as e:
        logger.error(str(e))
        return db_utils.format_response(500, {'error': str(e)})
    finally:
        if 'conn' in locals(): conn.close()