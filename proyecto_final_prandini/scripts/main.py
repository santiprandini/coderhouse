import requests
import pandas as pd
import os
import logging
import configparser
import sqlalchemy as sa
import logging
import psycopg2
import smtplib
from utils import resultado_partido, connect_to_db, build_conn_from_airflow_conn_id
from configparser import ConfigParser
from pathlib import Path
from sqlalchemy import create_engine
from airflow.models import Variable

# Configurar el logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def obtener_datos_desde_api():
    url_base = "https://www.thesportsdb.com"
    endpoint = "/api/v1/json/3/eventslast.php?id=133602"
    url = f"{url_base}/{endpoint}"

    resp = requests.get(url)

    if resp.status_code == 200:
        return resp.json()['results']
    else:
        error_msg = f"Error al obtener datos desde la API. Código de estado: {resp.status_code}, Contenido: {resp.content}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

def procesar_datos(data):
    df = pd.DataFrame(data)
    df['result'] = df.apply(resultado_partido, axis=1)
    return df

def enviar_correo_notificacion(row):
    try:
        x = smtplib.SMTP('smtp.gmail.com', 587)
        x.starttls()
        x.login('santiprandini@gmail.com', Variable.get('GMAIL_SECRET'))

        subject = 'Nuevo resultado negativo para Liverpool'
        body_text = f'Se ha registrado un resultado negativo para Liverpool.\n'
        body_text += f'Detalles: {row}'  
        message = f'Subject: {subject}\n\n{body_text}'

        x.sendmail('santiprandini@gmail.com', 'santiprandini@gmail.com', message)
        print('Correo enviado con éxito.')
    except Exception as e:
        print(f'Error al enviar el correo: {str(e)}')

def cargar_datos_a_bd(df, conn):
    schema = "santiprandini_coderhouse"

    conn.execute("""
        CREATE TABLE IF NOT EXISTS {schema}.liverpool (
          idevent VARCHAR,
          idSoccerXML VARCHAR,
          idAPIfootball VARCHAR,
          strEvent VARCHAR,
          strEventAlternate VARCHAR,
          strFilename VARCHAR,
          strSport VARCHAR,
          idLeague VARCHAR,
          strLeague VARCHAR,
          strSeason VARCHAR,
          strDescriptionEN VARCHAR,
          strHomeTeam VARCHAR,
          strAwayTeam VARCHAR,
          intHomeScore VARCHAR,
          intRound INT,
          intAwayScore INT,
          intSpectators INT,
          strOfficial VARCHAR,
          strTimestamp VARCHAR,
          dateEvent DATE,
          dateEventLocal DATE,
          strTime VARCHAR,
          strTimeLocal VARCHAR,
          strTVStation VARCHAR,
          idHomeTeam VARCHAR,
          idAwayTeam VARCHAR,
          intScore VARCHAR,
          intScoreVotes VARCHAR,
          strResult VARCHAR,
          strVenue VARCHAR,
          strCountry VARCHAR,
          strCity VARCHAR,
          strPoster VARCHAR,
          strSquare VARCHAR,
          strFanart VARCHAR,
          strThumb VARCHAR,
          strBanner VARCHAR,
          strMap VARCHAR,
          strTweet1 VARCHAR,
          strTweet2 VARCHAR,
          strTweet3 VARCHAR,
          strVideo VARCHAR,
          strStatus VARCHAR,
          strPostponed VARCHAR,
          strLocked VARCHAR,
          result VARCHAR,
          PRIMARY KEY (idEvent)
        )
        DISTSTYLE ALL
        sortkey(dateEvent)
;
    """.format(schema=schema))

    conn.execute("""
        DROP TABLE IF EXISTS {schema}.stage_liverpool;
        CREATE TABLE {schema}.stage_liverpool (
          idevent VARCHAR PRIMARY KEY,
          idSoccerXML VARCHAR,
          idAPIfootball VARCHAR,
          strEvent VARCHAR,
          strEventAlternate VARCHAR,
          strFilename VARCHAR,
          strSport VARCHAR,
          idLeague VARCHAR,
          strLeague VARCHAR,
          strSeason VARCHAR,
          strDescriptionEN VARCHAR,
          strHomeTeam VARCHAR,
          strAwayTeam VARCHAR,
          intHomeScore VARCHAR,
          intRound INT,
          intAwayScore INT,
          intSpectators INT,
          strOfficial VARCHAR,
          strTimestamp VARCHAR,
          dateEvent DATE,
          dateEventLocal DATE,
          strTime VARCHAR,
          strTimeLocal VARCHAR,
          strTVStation VARCHAR,
          idHomeTeam VARCHAR,
          idAwayTeam VARCHAR,
          intScore VARCHAR,
          intScoreVotes VARCHAR,
          strResult VARCHAR,
          strVenue VARCHAR,
          strCountry VARCHAR,
          strCity VARCHAR,
          strPoster VARCHAR,
          strSquare VARCHAR,
          strFanart VARCHAR,
          strThumb VARCHAR,
          strBanner VARCHAR,
          strMap VARCHAR,
          strTweet1 VARCHAR,
          strTweet2 VARCHAR,
          strTweet3 VARCHAR,
          strVideo VARCHAR,
          strStatus VARCHAR,
          strPostponed VARCHAR,
          strLocked VARCHAR,
          result VARCHAR
        );
    """.format(schema=schema))

    stage_liverpool = df.copy()

    eventos_existentes = pd.read_sql_query(
        "SELECT idEvent FROM liverpool",
        conn
    )

    stage_liverpool = pd.merge(
        stage_liverpool,
        eventos_existentes,
        on='idevent',
        how='left',
        indicator=True
    )

    stage_liverpool = stage_liverpool[stage_liverpool['_merge'] == 'left_only'].drop('_merge', axis=1)

    stage_liverpool.to_sql(
        name="liverpool",
        con=conn,
        schema=schema,
        if_exists="append",
        method="multi",
        index=False
    )

    resultados_liverpool = df[df['result'] == 'L']
    if not resultados_liverpool.empty:
        for index, row in resultados_liverpool.iterrows():
            enviar_correo_notificacion(row)

def main():
    conn_id = "coder_redshift"  #conn_id de conexión en Airflow
    schema = "santiprandini_coderhouse"  #esquema específico
    engine = build_conn_from_airflow_conn_id(conn_id, schema)
    if engine:
        conn, engine = connect_to_db(engine)  
        cargar_datos_a_bd(stage_liverpool, conn)
    else:
        error_msg = "Error al conectar a la base de datos."
        logger.error(error_msg)
        
if __name__ == "__main__":
    main()