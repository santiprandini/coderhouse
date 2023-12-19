from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.python_operator import PythonOperator
from utils import build_conn_from_airflow_conn_id, connect_to_db
from main import obtener_datos_desde_api, procesar_datos, cargar_datos_a_bd
import logging

default_args = {
    "retries": 3,
    "retry_delay": timedelta(minutes=1)
}

schema = "santiprandini_coderhouse"

def process_data_callable(**kwargs):
    ti = kwargs['ti']  # Obtenemos el objeto de la tarea
    obtained_data = ti.xcom_pull(task_ids='obtain_data_from_api')  # Obtenemos los datos del XCom
    procesar_datos(obtained_data)  # Llamamos a la función procesar_datos con los datos obtenidos

def load_data_callable(**kwargs):
    ti = kwargs['ti']
    processed_data = ti.xcom_pull(task_ids='process_data', key='processed_data')
    engine = build_conn_from_airflow_conn_id(conn_id="coder_redshit", schema=schema)
    
    if engine:
        logging.info("Conexión a la base de datos establecida correctamente.")
        conn, engine = connect_to_db(engine)
        
        if conn:
            logging.info("Conexión exitosa a la base de datos.")
            cargar_datos_a_bd(processed_data, conn)
        else:
            logging.error("La conexión no se pudo establecer.")
    else:
        logging.error("No se pudo obtener el motor de la base de datos.")


with DAG(
    dag_id="liverpool_dag",
    start_date=datetime(2023, 12, 15),
    catchup=False,
    schedule_interval="0 22 * * 0",  # Ejecución semanal los domingos a las 10 PM
    default_args=default_args
) as dag:

    dummy_start_task = DummyOperator(task_id="start")

    # Conexión a la base de datos
    connect_db_task = PythonOperator(
        task_id="connect_to_db",
        python_callable=build_conn_from_airflow_conn_id,  # Asegúrate de pasar los argumentos correctos aquí
        op_kwargs={
        "conn_id": "coder_redshit",
        "schema": schema
        }
    )

    # Obtener datos desde la API
    obtain_data_task = PythonOperator(
        task_id="obtain_data_from_api",
        python_callable=obtener_datos_desde_api,
        provide_context=True  # Esta línea es importante para pasar resultados entre tareas
    )

    # Procesar los datos obtenidos
    process_data_task = PythonOperator(
        task_id="process_data",
        python_callable=process_data_callable,
        provide_context=True  # Esta línea es importante para pasar resultados entre tareas
    )

    # Cargar datos procesados a la base de datos
    load_to_db_task = PythonOperator(
        task_id="load_data",
        python_callable=load_data_callable,
        provide_context=True
    )

    dummy_end_task = DummyOperator(task_id="end")

    # Define el orden de ejecución de las tareas
    dummy_start_task >> connect_db_task >> obtain_data_task >> process_data_task >> load_to_db_task >> dummy_end_task