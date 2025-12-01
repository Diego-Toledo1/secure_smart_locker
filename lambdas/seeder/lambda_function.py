import sys
import os
import pymysql
import logging

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

def lambda_handler(event, context):
    """
    Se conecta a RDS y ejecuta el script rds_schema.sql empaquetado.
    """
    conn = None
    try:
        logger.info(f"Intentando conectar a {rds_host}...")
        
        conn = pymysql.connect(
            host=rds_host, 
            user=name, 
            passwd=password, 
            connect_timeout=10
        )
        logger.info("Conexión exitosa a RDS.")
        
        with open('rds_schema.sql', 'r') as file:
            sql_script = file.read()
            
        statements = sql_script.split(';')
        
        with conn.cursor() as cur:
            # Seleccionar la DB primero por si acaso
            cur.execute(f"USE {db_name}") 
            for statement in statements:
                if statement.strip():
                    cur.execute(statement)
            conn.commit()
            
        logger.info("Script SQL ejecutado correctamente.")
        return {
            'statusCode': 200,
            'body': "Tablas creadas exitosamente en RDS."
        }
        
    except Exception as e:
        logger.error(f"Error crítico: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Error ejecutando seeder: {str(e)}"
        }
    finally:
        if conn:
            conn.close()