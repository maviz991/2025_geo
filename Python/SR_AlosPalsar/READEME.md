---

# Tutorial: Criando um Mosaico DEM de Larga Escala com ALOS PALSAR e Python

Este tutorial descreve o fluxo de trabalho completo para buscar, baixar e preparar dados de Modelos Digitais de Elevação (DEM) derivados de imagens de satélite ALOS PALSAR, com o objetivo de criar um mosaico para uma área extensa, como o estado de São Paulo.

## Etapa 0: Pré-requisitos

Antes de começar, garanta que você tenha:

1.  **Python 3.x** instalado.
2.  A biblioteca `asf_search` instalada [Github do projeto](https://github.com/asfadmin/Discovery-asf_search).
   
    ```bash
    pip install asf_search
    ```
    
4.  Uma conta no **NASA Earthdata Login** (essencial para o download). [Crie sua conta aqui](https://urs.earthdata.nasa.gov/users/new).
5.  Um software SIG para visualização, como o **QGIS** (gratuito e de código aberto).

## Etapa 1: Exploração (O Que Existe?)

Não podemos baixar dados às cegas. Primeiro, precisamos descobrir quais imagens estão disponíveis e onde elas estão localizadas. Para isso, geramos um arquivo geográfico (`.geojson`) com os contornos (footprints) de todas as cenas disponíveis para nossa área de interesse  `wkt_sp_retangulo`.
Mas para isso devemos nos guiar a partir de uma análise empirica das datas, através de `seach_date_analyse.py`, para filtramos as datas que vamos trabalhar a seguir.


#### 1.12 - Script de filtro temporal

Este script explora e os produtos disponíveis através de em uma lista de imagens disponíveis com: Nome (`fileID`), Data de aquisição (imageamento) e Direção da órbita.
Ele imprime no terminal a lista, para uma analise melhor gere um txt, executando dessa forma:

```bash
python seach_date_analyse.py > exp_protudo.txt
```

Então, a partir dessa análise você pode definir o espaço temporal de geração dos footprints de forma mais eficáz.

#### 1.2 - Script de Geração de Footprints

Este script busca todos os produtos ALOS PALSAR RTC sobre uma área `wkt_sp_retangulo` e salva seus footprints em um arquivo `footprints_sp.geojson`.

```python
# footprints_search.py
import asf_search as asf
import json

# Nome do arquivo de saída geográfico
output_filename_geojson = 'footprints_sp.geojson'

# (O resto dos parâmetros da busca é o mesmo)
wkt_sp_retangulo = 'POLYGON((-53.2 -25.4, -44.1 -25.4, -44.1 -19.7, -53.2 -19.7, -53.2 -25.4))'
opts = {
    'platform': asf.PLATFORM.ALOS,
    'intersectsWith': wkt_sp_retangulo,
    'processingLevel': asf.PRODUCT_TYPE.RTC_HIGH_RES,
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
```

#### 1.3 - Visualização no QGIS

1.  Abra o QGIS.
2.  Carregue um shapefile ou GeoJSON com o limite do seu estado/área.
3.  Arraste e solte o arquivo `footprints_sp.geojson` gerado no painel de camadas.
4.  Você verá todos os contornos das imagens sobrepostos ao mapa, permitindo uma análise visual da cobertura.

## Etapa 2: Seleção (Escolhendo as Imagens Corretas)

Nosso objetivo é selecionar o **menor número de imagens** que garantam **cobertura total**, preferencialmente de datas próximas e da mesma órbita para maior consistência.

1.  **Identifique as "Faixas":** No QGIS, você notará que as imagens de uma mesma data formam uma "faixa" contínua.
2.  **Selecione as Cenas:** Use a ferramenta de seleção do QGIS para selecionar interativamente as faixas e cenas individuais necessárias para "pintar" toda a sua área de interesse, sem deixar buracos.
3.  **Exporte a Lista de Nomes:**
    *   Com as cenas necessárias selecionadas, clique com o botão direito na camada de footprints e abra a **Tabela de Atributos**.
    *   Filtre para mostrar apenas as feições selecionadas.
    *   Selecione e copie a coluna com os nomes das cenas (geralmente `fileID`) - poderá gerar um CSV → TXT (UTF-8).
    *   Cole esta lista em um novo arquivo de texto chamado `list_imag.txt` em `UTF-8`, com um nome de cena por linha.

## Etapa 3: Download e Extração Otimizados

Para evitar o download de Terabytes de dados desnecessários, usamos um script que baixa um arquivo por vez, extrai **apenas o DEM**, e deleta o arquivo compactado para liberar espaço.

Este script é robusto e lida com diferentes convenções de nomes de arquivos (`_dem.tif` vs `.dem.tif`) e com a estrutura de pastas dentro dos arquivos `.zip`.

```python
# script_02_download_otimizado.py
import asf_search as asf
from getpass import getpass
import os
import zipfile
import shutil

# --- CONFIGURAÇÕES ---
download_path = 'temp_downloads'
dem_path = 'dems_finais_sp'
granule_list_file = 'list_imag.txt'

os.makedirs(download_path, exist_ok=True)
os.makedirs(dem_path, exist_ok=True)

try:
    # --- Ler a lista de grânulos do arquivo de texto ---
    with open(granule_list_file, 'r') as f:
        lista_de_granulos = [line.strip() for line in f if line.strip()]
    print(f"{len(lista_de_granulos)} imagens serão processadas.")

    # --- Autenticação ---
    session = asf.ASFSession()
    username = input("Digite seu usuário do NASA Earthdata: ")
    password = getpass("Digite sua senha do NASA Earthdata: ")
    session.auth_with_creds(username, password)

    # --- Busca pela lista de grânulos ---
    results = asf.granule_search(lista_de_granulos)

    # --- Loop Otimizado ---
    for index, product in enumerate(results):
        zip_filename = product.properties['fileName']
        zip_filepath = os.path.join(download_path, zip_filename)
        
        print(f"\n({index + 1}/{len(results)}) Processando: {zip_filename}")
        try:
            # 1. Baixar o zip
            product.download(path=download_path, session=session)
            
            # 2. Encontrar e extrair o DEM de forma robusta
            with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
                dem_files = [
                    name for name in zip_ref.namelist() 
                    if name.lower().endswith('_dem.tif') or name.lower().endswith('.dem.tif')
                ]
                
                if dem_files:
                    full_dem_path_in_zip = dem_files[0]
                    dem_basename = os.path.basename(full_dem_path_in_zip)
                    dest_filepath = os.path.join(dem_path, dem_basename)
                    
                    with zip_ref.open(full_dem_path_in_zip) as source_file:
                        with open(dest_filepath, 'wb') as dest_file:
                            shutil.copyfileobj(source_file, dest_file)
                    print(f"   ✅ - DEM '{dem_basename}' salvo com sucesso!")
                else:
                    print(f"    - AVISO: Nenhum arquivo DEM encontrado neste zip.")

        except Exception as e:
            print(f"   ❌ - ERRO ao processar o arquivo: {e}")
        
        finally:
            # 3. Deletar o zip para liberar espaço
            if os.path.exists(zip_filepath):
                os.remove(zip_filepath)

    print("\n\nm  🆗 Processo concluído!")

except Exception as e:
    print(f"\nOcorreu um erro geral: {e}")
```

## Etapa 4: Mosaico (Juntando as Peças)

Com a pasta `dems_finais_sp` cheia de arquivos `.tif`, o passo final é uni-los em um único raster.

1.  Abra o QGIS.
2.  Vá no menu **Raster -> Miscelânea -> Mosaico (Merge)**.
3.  Na janela que abrir, clique no botão `...` ao lado de "Camadas de entrada".
4.  Clique em "Adicionar Arquivos" e selecione **todos** os arquivos `.tif` da sua pasta `dems_finais_sp`.
5.  Em "Mosaico", escolha um local e nome para salvar o seu DEM final (ex: `DEM_SP_12.5m.tif`).
6.  Execute o processo. Ao final, você terá um único arquivo com o DEM completo da sua área.

---

## Conceitos-Chave e Lições Aprendidas

*   **Footprint vs. Imagem Corrigida:** O footprint (inclinado) representa a geometria da captura do satélite. O DEM (retangular, alinhado ao norte) é o produto final após a correção geométrica (ortorretificação). O desalinhamento entre eles é normal e esperado.
*   **Resolução do DEM:** Os arquivos DEM nos produtos ALOS PALSAR RTC de 12.5m são derivados de fontes de ~30m (como o Copernicus DEM). Eles são **reamostrados** para 12.5m para corresponder à grade da imagem de radar, mas a resolução efetiva da informação de relevo é de 30m.
*   **Robustez do Código:** Ao lidar com grandes arquivos de dados, é crucial escrever código que antecipe problemas, como arquivos ausentes, inconsistências nos nomes (`_dem.tif` vs `.dem.tif`) e estruturas de pastas inesperadas.
