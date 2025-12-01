import os
import pymysql
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_db_connection():
    """
    Crea una conexión a la base de datos usando variables de entorno.
    """
    try:
        # Nota: Aquí usaremos 'smartlocker_db' directamente
        conn = pymysql.connect(
            host=os.environ['RDS_HOST'],
            user=os.environ['RDS_USER'],
            passwd=os.environ['RDS_PASSWORD'],
            db=os.environ['RDS_DB_NAME'],
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=5
        )
        return conn
    except Exception as e:
        logger.error(f"ERROR: No se pudo conectar a RDS. Detalle: {str(e)}")
        raise e

def format_response(status_code, body):
    """
    Genera la respuesta estándar para API Gateway con CORS habilitado.
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',  # Importante para React local
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(body, default=str)
    }