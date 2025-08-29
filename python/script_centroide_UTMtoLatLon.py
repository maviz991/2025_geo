import geopandas as gpd
import pandas as pd
import pyodbc
import time

# --- CONFIGURAÇÔES ---
conn_str = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=end_servidor;'
    r'DATABASE=id_banco;'
    r'Trusted_Connection=yes;'
    #r'UID=id_user;'
    #r'PWD=id_senha;'
)

ZONA_22S_CONFIG = { 
    "nome_tabela": "[SCHEMA].[TABELA]",
    "coluna_geom": "CAMPO_GEOM",
    "coluna_lat": "CAMPO_ATUALIZAR",
    "coluna_lon": "CAMPO_ATUALIZAR",
    "epsg_origem": "EPSG:31982"
}
ZONA_23S_CONFIG = { 
    "nome_tabela": "[SCHEMA].[TABELA]",
    "coluna_geom": "CAMPO_GEOM",
    "coluna_lat": "CAMPO_ATUALIZAR",
    "coluna_lon": "CAMPO_ATUALIZAR",
    "epsg_origem": "EPSG:31983"
}

# --- FUNÇÃO ---
def processar_zona_com_geopandas(config):
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

        update_query = f"UPDATE {nome_tabela} SET {config['coluna_lat']} = ?, {config['coluna_lon']} = ? WHERE qgs_fid = ?"
        
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
if __name__ == "__main__":
    processar_zona_com_geopandas(ZONA_22S_CONFIG)
    processar_zona_com_geopandas(ZONA_23S_CONFIG)
