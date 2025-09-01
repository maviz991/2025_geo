from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
from airflow.models import Variable
import pendulum, requests, pyodbc
from datetime import datetime, timedelta
import geopandas as gpd
import pandas as pd
import time

def get_corporativo_connection():
    # --- CONFIGURAÇÔES ---
    conn = BaseHook.get_connection('Hml_DB_ID-DB')
    conn_str = (
        f"DRIVER={conn.extra_dejson.get('Driver', 'ODBC Driver 18 for SQL Server')};"
        f"SERVER={conn.host};"
        f"DATABASE={conn.schema};"
        f"UID={conn.login};"
        f"PWD={conn.password};"
        f"PORT={conn.port or '1234'};"
        f"TrustServerCertificate={conn.extra_dejson.get('TrustServerCertificate', 'yes')};"
    )
    return pyodbc.connect(conn_str)  

# --- FUNÇÃO ---
def processar_zona_com_geopandas(config):

    conn_str = get_corporativo_connection()

    nome_tabela = config["nome_tabela"]
    coluna_geom = config["coluna_geom"]
    
    print(f"\n--- INICIANDO PROCESSAMENTO COM LÓGICA NO GEOPANDAS PARA: {nome_tabela} ---")
    start_time = time.time()
    
    try:
        # ETAPA 1: LEITURA DOS DADOS BRUTOS
        query_leitura = f"""
            SELECT qgs_fid, {coluna_geom}.STAsBinary() AS geometry
            FROM {nome_tabela}"""
        
        print("1. Lendo geometrias MS SQL Server...")
        
        with pyodbc.connect(conn_str, timeout=300) as conn:
            df = pd.read_sql(query_leitura, conn)
        
        # Filtra qualquer linha que o STAsBinary() não conseguiu processar (raro, mas seguro)
        df.dropna(subset=['geometry'], inplace=True)
        
        print(f"Leitura concluída. {len(df)} registros encontrados.")
        if df.empty:
            print("Nenhum dado para processar.")
            return

        gdf = gpd.GeoDataFrame(df, geometry=gpd.GeoSeries.from_wkb(df['geometry']), crs=config["epsg_origem"])
        print("GeoDataFrame criado com sucesso.")

        # ETAPA 2: PROCESSAMENTO E CÁLCULO DO CENTROIDE (Removi o cálculo do banco)
        print("2. Calculando centroides no Geopandas...")
        gdf['geometry'] = gdf.geometry.centroid
               
        # Filtro: remove geometrias que resultaram em centroides vazios
        registros_antes_filtro = len(gdf)
        gdf = gdf[~gdf.geometry.is_empty]
        registros_depois_filtro = len(gdf)
        
        if registros_antes_filtro > registros_depois_filtro:
            print(f"ATENÇÃO: {registros_antes_filtro - registros_depois_filtro} registros foram pulados porque não foi possível calcular um centroide.")

        #Reprojeção em si
        print("3. Reprojetando os centroides para Lat/Lon EPSG:4674...")
        gdf_latlon = gdf.to_crs("EPSG:4674")
        
        gdf[config["coluna_lat"]] = gdf_latlon.geometry.y
        gdf[config["coluna_lon"]] = gdf_latlon.geometry.x
        print("   Processamento concluído!")

        # ETAPA 4: ATUALIZAÇÃO EM LOTE
        print(f"4. Atualizando {len(gdf)} registros no banco de dados...")
        dados_para_atualizar = list(zip(
            gdf[config["coluna_lat"]],
            gdf[config["coluna_lon"]],
            gdf['qgs_fid']
        ))

        update_query = f"""
            UPDATE {nome_tabela} 
            SET {config['coluna_lat']} = ?, {config['coluna_lon']} = ? 
            WHERE qgs_fid = ?
         """
        
        with pyodbc.connect(conn_str) as conn:
            with conn.cursor() as cursor:
                cursor.fast_executemany = True
                cursor.executemany(update_query, dados_para_atualizar)
                conn.commit()
        
        print(f"A tabela '{nome_tabela}' foi atualizada!")

    except Exception as e:
        print(f"ERRO: {e}")
    finally:
        end_time = time.time()
        print(f"Tempo de execução: {end_time - start_time:.2f} segundos.")

# --- PONTO DE ENTRADA DO SCRIPT ---
# if __name__ == "__main__":
#     processar_zona_com_geopandas(ZONA_22S_CONFIG)
#     processar_zona_com_geopandas(ZONA_23S_CONFIG)

default_args = {
      'owner': 'Matheus Dias Aviz',
      'depends_on_past': False,
      'start_date': pendulum.datetime(2025, 8, 29, tz='America/Sao_Paulo'),
      'retries': 1,
      'retry_delay': timedelta(minutes=5),
      'execution_timeout': timedelta(minutes=30)
  }
with DAG(
      dag_id='hml_atualizacao_centroide_latlon',
      default_args=default_args,
      description='Executa query no banco Corporativo e altera valor de centroides latitude e longitude.',
      schedule= None, #'0 0 24 8 *',
      catchup=False,
      tags=['geopandas', 'geoprocessamento', 'etl'],
) as dag:
    def processar_zona_22s():
        config = {
            "nome_tabela": "[SCHEMA].[tbOrigem]",
            "coluna_geom": "Campo_Geom",
            "coluna_lat": "CampoLat",
            "coluna_lon": "CampoLon",
            "epsg_origem": "EPSG:31982"
        }
        processar_zona_com_geopandas(config)

    def processar_zona_23s():
        config = {
            "nome_tabela": "[SCHEMA].[tbOrigem]",
            "coluna_geom": "Campo_Geom",
            "coluna_lat": "CampoLat",
            "coluna_lon": "CampoLon",
            "epsg_origem": "EPSG:31983"
        }
        processar_zona_com_geopandas(config)
    
    task_zona_22s = PythonOperator(
        task_id='processar_zona_22s',
        python_callable=processar_zona_22s
    )

    task_zona_23s = PythonOperator(
        task_id='processar_zona_23s',
        python_callable=processar_zona_23s
    )
    task_zona_22s >> task_zona_23s
