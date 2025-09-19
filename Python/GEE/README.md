---

# Tutorial Definitivo: Gerando um DEM com Google Earth Engine (Python) via Terminal

Este tutorial descreve o fluxo de trabalho completo para processar e exportar um Modelo Digital de Elevação (DEM) para uma área extensa, utilizando o poder da nuvem do Google Earth Engine (GEE) através de um script Python executado localmente.

Esta abordagem é a mais eficiente, pois **evita o download de grandes volumes de dados**, delegando todo o processamento pesado aos servidores do Google.

## Objetivo

Gerar um único arquivo GeoTIFF contendo o DEM do Copernicus 30m para uma área definida (neste caso, o estado de São Paulo) e salvá-lo diretamente no Google Drive.

## Etapa 0: Pré-requisitos

1.  **Python e Ambiente Virtual (`venv`):** Um ambiente Python isolado para instalar as bibliotecas [Veja qui como instalar](https://github.com/maviz991/tutorial/blob/main/tutorial_install_py_linux.md).
2.  **Conta no Google Earth Engine:** É necessário ter o acesso aprovado. [Solicite aqui, se necessário](https://signup.earthengine.google.com/).
3.  **Biblioteca `earthengine-api`:** A API oficial do Google para interagir com o GEE.
Dentro do seu ambiente venv ativado
  ```bash
  pip install earthengine-api
  ```
E instale:
  ```bash
  pip install gcloud
  ```

## Etapa 1: O Script de Processamento (com Autenticação Integrada)

Diferente de outros métodos, a abordagem mais robusta para um ambiente de terminal é integrar a autenticação diretamente no script. Ele tentará se conectar e, se for a primeira vez, guiará você pelo processo de autenticação.

Salve este código em um arquivo, por exemplo `gerar_dem_gee.py`.

```python
# gerar_dem_gee.py

import ee

# --------------------------------------------------------------------------
# PASSO 1: AUTENTICAÇÃO E INICIALIZAÇÃO
# Este bloco 'try...except' lida com a autenticação na primeira execução.
# --------------------------------------------------------------------------
try:
    # Tenta inicializar. Se as credenciais já existirem, funciona direto.
    ee.Initialize()
except Exception as e:
    # Se falhar, significa que é a primeira vez ou as credenciais expiraram.
    print("Primeira autenticação necessária. Siga as instruções...")
    
    # Força o método de autenticação interativo (baseado em link),
    # que funciona perfeitamente no terminal.
    ee.Authenticate(auth_mode='notebook')
    
    # Tenta inicializar novamente após a autenticação bem-sucedida.
    ee.Initialize()

print("Conexão com o Google Earth Engine estabelecida com sucesso!")

# --------------------------------------------------------------------------
# PASSO 2: DEFINIR A ÁREA DE INTERESSE (ESTADO DE SÃO PAULO)
# --------------------------------------------------------------------------
aoi_sp = ee.Geometry.Rectangle([-53.2, -25.4, -44.1, -19.7])

# --------------------------------------------------------------------------
# PASSO 3: PROCESSAMENTO EM NUVEM
# --------------------------------------------------------------------------
# 1. Carrega a ImageCollection do Copernicus DEM (GLO30) e filtra pela nossa área.
dem_collection = ee.ImageCollection('COPERNICUS/DEM/GLO30').filterBounds(aoi_sp)

# 2. Seleciona a banda de elevação, que se chama 'DEM'.
dem_band = dem_collection.select('DEM')

# 3. Usa .median() para criar um mosaico robusto e de alta qualidade e o corta.
dem_sp = dem_band.median().clip(aoi_sp)

print("Receita de processamento montada. O DEM de São Paulo está pronto para ser exportado.")

# --------------------------------------------------------------------------
# PASSO 4: EXPORTAR O RESULTADO FINAL PARA O GOOGLE DRIVE
# --------------------------------------------------------------------------
task = ee.batch.Export.image.toDrive(
  image=dem_sp,
  description='DEM_Sao_Paulo_Copernicus_GLO30',
  folder='GEE_Exports',
  region=aoi_sp,
  scale=30,
  maxPixels=1e13,
  fileFormat='GeoTIFF',
  formatOptions={'cloudOptimized': True}
)

# Inicia a tarefa de exportação nos servidores do GEE
task.start()

print("\nExportação iniciada com sucesso!")
print("O script no seu terminal já pode ser fechado. A tarefa continuará na nuvem.")
print("Para acompanhar o progresso, acesse a aba 'Tasks' no GEE Code Editor:")
print("https://code.earthengine.google.com/tasks")
print(f"ID da tarefa: {task.id} | Status inicial: {task.status()['state']}")
```

## Etapa 2: Execução e Monitoramento

1.  **Execute o script** no seu terminal (com o `venv` ativado):
    ```bash
    python gerar_dem_gee.py
    ```
2.  **Autenticação (somente na primeira vez):**
    *   O script imprimirá "Primeira autenticação necessária..." e fornecerá um **link**.
    *   Copie o link e cole em um navegador.
    *   Faça login com sua conta Google e permita o acesso.
    *   O Google fornecerá um **código de autorização**. Copie-o.
    *   Cole o código de volta no seu terminal e pressione `Enter`.

3.  **Acompanhe a Saída:** O script irá então se conectar, montar as instruções e iniciar a tarefa. Ao final, ele imprimirá o status e o link para monitoramento. O script local será encerrado, o que é o comportamento esperado.

4.  **Monitore na Web:**
    *   Acesse o link: [https://code.earthengine.google.com/tasks](https://code.earthengine.google.com/tasks)
    *   Você verá sua tarefa (`DEM_Sao_Paulo_Copernicus_GLO30`) na lista.
    *   Quando a tarefa for concluída (marcada com um `✓` verde), o arquivo `.tif` estará na pasta `GEE_Exports` do seu Google Drive.

## Resumo Esquemático do Fluxo de Trabalho

```mermaid
graph TD
    subgraph Local (Seu Computador)
        A[Terminal com venv] -->|executa| B[Script Python: gerar_dem_gee.py];
        B -->|na 1ª vez| C{Autenticação via Link/Token};
        C --> D{Credenciais Salvas};
    end

    subgraph Nuvem (Servidores do Google)
        E[Google Earth Engine] --> F[Dataset: Copernicus DEM];
        F --> G[Processamento: Median + Clip];
        G --> H[Tarefa de Exportação];
        I[Google Drive]
    end
    
    B -->|envia instruções| E;
    H -->|salva o arquivo| I;

    style D fill:#d4edda,stroke:#155724
    style I fill:#d4edda,stroke:#155724
```
