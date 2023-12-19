import pandas as pd
import sqlalchemy as sa
import logging
from configparser import ConfigParser
from sqlalchemy import create_engine
from pathlib import Path

def resultado_partido(row):
    if row['intHomeScore'] > row['intAwayScore']:
        return 'W'  # Equipo local ganó
    elif row['intHomeScore'] < row['intAwayScore']:
        return 'L'  # Equipo local perdió
    else:
        return 'T'  # Empate

def build_conn_from_airflow_conn_id(conn_id, schema):
    try:
        engine = create_engine(f'airflow://{conn_id}')
        logging.info("Conexión a la base de datos establecida exitosamente")
        return engine
    except Exception as e:
        logging.error(f"Error al conectarse a la base de datos: {e}")
        return None

def connect_to_db(engine):
    conn = engine.connect()
    return conn, engine