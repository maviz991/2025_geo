#Use search_date_analyse.py para ajustar o ínicio e fim das datas
import asf_search as asf
import json

# Saída .geojson
output_filename_geojson = 'footprints_sp.geojson'

# Parâmetros da busca
wkt_sp_retangulo = 'POLYGON((-53.2 -25.4, -44.1 -25.4, -44.1 -19.7, -53.2 -19.7, -53.2 -25.4))'
opts = {
    'platform': asf.PLATFORM.ALOS,
    'intersectsWith': wkt_sp_retangulo,
    'processingLevel': asf.PRODUCT_TYPE.RTC_HIGH_RES, #Produto de alta resolução 12.5m → 'RTC_HIGH_RES'
    'beamMode': [asf.BEAMMODE.FBS, asf.BEAMMODE.FBD],
    'start': '2011-01-13T02:27:54Z',
    'end': '2011-03-17T02:30:08Z'
}

try:
    print("Iniciando busca por footprints...")
    results = asf.search(**opts)
    total_results = len(results)
    print(f"Busca concluída. {total_results} resultados encontrados.")
    
    if total_results > 0:
        print(f"Salvando os footprints em '{output_filename_geojson}' (Método Manual)...")
        
        # Pega os dados geojson do resultado
        geojson_data = results.geojson()
        
        # Escreve os dados em um arquivo
        with open(output_filename_geojson, 'w') as f:
            json.dump(geojson_data, f, indent=2)
        
        print("Arquivo GeoJSON salvo com sucesso!")

except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")
