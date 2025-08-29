
import geopandas as gpd
import pandas as pd
import pyodbc
import time

# --- CONFIGURAÇÃO DA CONEXÃO ---
conn_str = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=end_servidor;'
    r'DATABASE=id_banco;'
    r'Trusted_Connection=yes;'
    #r'UID=id_user;'
    #r'PWD=id_senha;'
)

# --- FUNÇÃO DE LÓGICA REUTILIZÁVEL ---
def processar_zona_com_geopandas(config):
    nome_tabela = config["nome_tabela"]
    coluna_geom = config["coluna_geom"]
    
    print(f"\n--- INICIANDO PROCESSAMENTO PARA: {nome_tabela} ---")
    start_time = time.time()
    
    try:
        # ETAPA 1: LEITURA DOS DADOS BRUTOS
        query_leitura = f"""
            SELECT qgs_fid, {coluna_geom}.STAsBinary() AS geometry
            FROM {nome_tabela}
            WHERE {coluna_geom} IS NOT NULL AND {coluna_geom}.STIsEmpty() = 0;
        """
        print("1. Lendo geometrias do MS SQL Server...")
        
        with pyodbc.connect(conn_str, timeout=300) as conn:
            df = pd.read_sql(query_leitura, conn)
        
        df.dropna(subset=['geometry'], inplace=True)
        
        print(f"   Leitura concluída. {len(df)} registros encontrados.")
        if df.empty: return

        gdf = gpd.GeoDataFrame(df, geometry=gpd.GeoSeries.from_wkb(df['geometry']), crs=config["epsg_origem"])
        print("   GeoDataFrame criado com sucesso.")

        # ETAPA 2: PROCESSAMENTO E CÁLCULO DO CENTROIDE
        print("2. Calculando centroides no Geopandas...")
        gdf['geometry'] = gdf.geometry.centroid
        
        registros_antes = len(gdf)
        gdf = gdf[~gdf.geometry.is_empty]
        registros_depois = len(gdf)
        
        if registros_antes > registros_depois:
            print(f"   ATENÇÃO: {registros_antes - registros_depois} registros foram pulados porque não foi possível calcular um centroide válido.")

        # ETAPA 3: REPROJEÇÃO
        print(f"3. Reprojetando {len(gdf)} centroides para Lat/Lon (EPSG:4674)...")
        gdf_latlon = gdf.to_crs("EPSG:4674")
        
        # --- A CORREÇÃO ESTÁ AQUI ---
        gdf[config["coluna_lat"]] = gdf_latlon.geometry.y
        gdf[config["coluna_lon"]] = gdf_latlon.geometry.x
        print("   Reprojeção concluída!")

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
        
        print(f"   ✅ SUCESSO! A tabela '{nome_tabela}' foi atualizada.")

    except Exception as e:
        print(f"   ❌ ERRO: {e}")
    finally:
        end_time = time.time()
        print(f"   Tempo de execução: {end_time - start_time:.2f} segundos.")

# --- PONTO DE ENTRADA DO SCRIPT ---
if __name__ == "__main__":
    
    ZONA_22S_CONFIG = { 
        "nome_tabela": "[SCHEMA].[TbOrigem]",
        "coluna_geom": "Campo_Geom",
        "coluna_lat": "Campo_Latitude",
        "coluna_lon": "Campo_Longitude",
        "epsg_origem": "EPSG:31982"
    }

    ZONA_23S_CONFIG = { 
        "nome_tabela": "[SCHEMA].[TbOrigem]",
        "coluna_geom": "Campo_Geom",
        "coluna_lat": "Campo_Latitude",
        "coluna_lon": "Campo_Longitude",
        "epsg_origem": "EPSG:31982"
    }

    print("Iniciando fluxo de atualização de coordenadas.")
    
    processar_zona_com_geopandas(ZONA_22S_CONFIG)
    processar_zona_com_geopandas(ZONA_23S_CONFIG)

    print("Fluxo de atualização finalizado.")
