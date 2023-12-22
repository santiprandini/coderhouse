import pandas as pd
import sqlalchemy as sa
import logging
import configparser
import psycopg2
from configparser import ConfigParser
from sqlalchemy import create_engine
from pathlib import Path
from airflow.hooks.base_hook import BaseHook

def resultado_partido(row):
    if row['intHomeScore'] > row['intAwayScore']:
        return 'W'  # Equipo local ganó
    elif row['intHomeScore'] < row['intAwayScore']:
        return 'L'  # Equipo local perdió
    else:
        return 'T'  # Empate

def build_conn_from_airflow_conn_id(conn_id, schema):
    try:
        conn = BaseHook.get_connection(conn_id)
        engine_url = conn.get_uri()
        engine = create_engine(engine_url)
        logging.info(f"Conexión a la base de datos establecida exitosamente. URL: {engine_url}")
        return engine
    except Exception as e:
        error_msg = f"Error al conectarse a la base de datos URL: {engine_url}: {e}"
        logging.error(error_msg)
        raise  # Levanta la excepción para indicar un problema en la conexión

def connect_to_db(engine):
    try:
        conn = engine.connect()
        return conn, engine
    except Exception as e:
        error_msg = f"Error al conectarse a la base de datos: {e}"
        logging.error(error_msg)
        raise  # Levanta la excepción si hay un problema en la conexión