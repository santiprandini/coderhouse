import smtplib
import logging
import configparser
import psycopg2
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.python_operator import PythonOperator
from utils import build_conn_from_airflow_conn_id, connect_to_db
from main import enviar_correo_notificacion, obtener_datos_desde_api, procesar_datos, cargar_datos_a_bd
from airflow.models import Variable

default_args = {
    "retries": 2,
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
        conn = connect_to_db(engine)  # Obtener solo la conexión
        
        if conn:
            logging.info("Conexión exitosa a la base de datos.")
            cargar_datos_a_bd(processed_data, conn)
        else:
            error_msg = "La conexión no se pudo establecer."
            logging.error(error_msg)
    else:
        error_msg = "No se pudo obtener el motor de la base de datos."
        logging.error(error_msg)

def enviar_email(**context):
    try:
        x = smtplib.SMTP('smtp.gmail.com', 587)
        x.starttls()
        
        x.login('santiprandini@gmail.com', Variable.get('GMAIL_sECRET'))
        
        # Construyendo el mensaje de correo
        subject = f'Error en la ejecución del DAG {context["dag"]} el {context["ds"]}'
        body_text = f'La tarea {context["task_instance_key_str"]} ha fallado durante la ejecución del DAG.\n'
        body_text += f'Por favor, revisa el registro de Airflow para más detalles.'

        # Convertir el mensaje a UTF-8
        subject = subject.encode('utf-8')
        body_text = body_text.encode('utf-8')

        message = f'Subject: {subject}\n\n{body_text}'

        # Enviando el correo
        x.sendmail('santiprandini@gmail.com', 'santiprandini@gmail.com', message)
        print('Correo enviado con éxito.')
    except Exception as exception:
        print(f'Error al enviar el correo: {exception}')

with DAG(
    dag_id="liverpool_dag",
    start_date=datetime(2023, 12, 15),
    catchup=False,
    schedule_interval="0 22 * * 0",  # Ejecución semanal los domingos a las 10 PM
    default_args=default_args
) as dag:

    # Conexión a la base de datos
    connect_db_task = PythonOperator(
        task_id="connect_to_db",
        python_callable=build_conn_from_airflow_conn_id,  
        op_kwargs={
        "conn_id": "coder_redshit",
        "schema": schema,
        }
    )

    # Obtener datos desde la API
    obtain_data_task = PythonOperator(
        task_id="obtain_data_from_api",
        python_callable=obtener_datos_desde_api,
        provide_context=True  
    )

    # Procesar los datos obtenidos
    process_data_task = PythonOperator(
        task_id="process_data",
        python_callable=process_data_callable,
        provide_context=True  
    )

    # Cargar datos procesados a la base de datos
    load_to_db_task = PythonOperator(
        task_id="load_data",
        python_callable=load_data_callable,
        provide_context=True
    )

    # Enviar mail en caso de que una tarea falle
    send_email_task = PythonOperator(
        task_id="send_email_on_failure",
        python_callable=enviar_email,
         provide_context=True,
        trigger_rule="one_failed"  # Se ejecutará si alguna tarea falla en el DAG
    )
  
    # Define el orden de ejecución de las tareas
    connect_db_task >> obtain_data_task >> process_data_task >> load_to_db_task
    [load_to_db_task, process_data_task, obtain_data_task, connect_db_task] >> send_email_task