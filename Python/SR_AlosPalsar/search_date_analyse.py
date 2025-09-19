import asf_search as asf

# Script para EXPLORAR os dados disponíveis, sem baixar.

# Parâmetros da busca - comente 'start' e 'end' para ver todos os produtos disponíveis.
wkt_municipio_sp = 'POLYGON((-53.2 -25.4, -44.1 -25.4, -44.1 -19.7, -53.2 -19.7, -53.2 -25.4))'
opts = {
    'platform': asf.PLATFORM.ALOS,
    'intersectsWith': wkt_municipio_sp,
    'processingLevel': asf.PRODUCT_TYPE.RTC_HIGH_RES,
    'beamMode': [asf.BEAMMODE.FBS, asf.BEAMMODE.FBD],
    'start': '2011-01-13T02:27:54Z',
    'end': '2011-03-17T02:30:08Z'
}

try:
    print("Iniciando busca exploratória...")
    results = asf.search(**opts)
    print(f"Busca concluída. Total de {len(results)} resultados encontrados.")
    
    if len(results) > 0:
        print("\nLista de imagens disponíveis (Nome, Data de aquisição, Direção da órbita):")
        # Itera sobre os resultados e imprime as informações chave
        for product in results:
            print(
                f"- {product.properties['sceneName']}, "
                f"Data: {product.properties['startTime']}, "
                f"Órbita: {product.properties['flightDirection']}"
            )
        
        print("\nPróximo passo: Analise a lista acima e escolha um conjunto de imagens da mesma órbita")
        print("e de um período de tempo curto que cubra sua área. Depois, adicione um filtro")
        print("de data ('start' e 'end') ao script de download para baixar apenas essas imagens.")

except Exception as e:
    print(f"Ocorreu um erro: {e}")

#gere um txt se o terminal não suportar com o comando: python search_date_analyse.py > exp_protudos.txt
