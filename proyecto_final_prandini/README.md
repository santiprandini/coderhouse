# You'll never walk alone

El proyecto consiste en un ETL (Extract, Transform, Load) que se encarga de recopilar y almacenar los resultados de los partidos en los que el equipo Liverpool juega como local. Extrae datos de una fuente externa, procesa la información para determinar si el equipo ganó o perdió, y almacena estos resultados en una tabla. Además, en caso de que esté disponible, guarda un enlace al video con el resumen del partido.

Este proceso se realiza de manera automatizada utilizando Python, pandas para el procesamiento de datos, y sqlalchemy para la interacción con la base de datos. Se implementa en un entorno de Airflow, asegurando la ejecución periódica y controlada de las tareas.

El objetivo principal es mantener actualizada una base de datos con los resultados de los partidos del Liverpool como local, facilitando el análisis histórico y proporcionando acceso rápido a los resúmenes de los juegos cuando están disponibles.


# Tabla de Contenidos

* Requisitos
* Configuración del Entorno
* Ejecución
* Estructura del Proyecto
* Contribución
* Licencia


## Requisitos

- Python 3.x
- Librerías: pandas, sqlalchemy, requests, configparser
- PostgreSQL (puede ser ejecutado en Docker utilizando el archivo docker-compose.yml provisto)


## Configuración del Entorno
### 1 - Clonar el Repositorio
git clone <Uhttps://github.com/santiprandini/coderhouse>

### 2 - Instalar Dependencias
pip install -r requirements.txt

### 3 - Configurar Variables de Entorno 
Asegúrate de configurar las variables de entorno necesarias, tales como conn_id para la conexión a la base de datos en Airflow.


## Ejecución
Pasos necesarios para ejecutar el proyecto:

### 1 - Obtener datos desde la API.
python main.py

### 2 - Ejecutar el DAG en Airflow.
docker-compose up


## Estructura del Proyecto
/
|- main.py          # Punto de entrada principal del proyecto
|- utils.py         # Funciones utilitarias
|- DAGs/            # Directorio con los archivos de DAGs de Airflow
|   |- liverpool_dag.py
|- docker-compose.yml  # Archivo de configuración para ejecutar el proyecto en Docker
|- README.md        # Este archivo
|- requirements.txt # Lista de dependencias del proyecto
|- config/          # Directorio con archivos de configuración
   |- ...
|- scripts/         # Scripts adicionales o de apoyo
   |- ...


## Contribución
Si quieres contribuir a este proyecto, sigue estos pasos:

Haz un fork del repositorio.
Crea una nueva rama (git checkout -b feature/nueva-caracteristica).
Realiza tus cambios.
Haz commit de tus cambios (git commit -am 'Agrega nueva característica').
Haz push a la rama (git push origin feature/nueva-caracteristica).
Crea un Pull Request.


