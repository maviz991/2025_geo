# Documentação do Script: Gerador de Metadados MGB 2.0 (csvToXML_metadata.py)

## 1. Visão Geral
Este script automatiza a criação de múltiplos arquivos de metadados XML, seguindo o padrão **MGB 2.0 BR** (baseado na norma ISO 19115). Ele utiliza um arquivo CSV como fonte de dados e um arquivo XML como template estrutural.

Para cada linha de dados no arquivo CSV, o script gera um novo arquivo XML, preenchendo os campos correspondentes do template. Ele é projetado para ser robusto, garantindo que a estrutura do XML gerado seja válida e compatível com sistemas de gerenciamento de metadados, como o **GeoNetwork**.

---

## 2. Pré-requisitos
Antes de executar o script, certifique-se de que você tem:

- Python 3.x instalado.
- As bibliotecas Python necessárias. Para instalá-las, execute no terminal:

```bash
pip install pandas lxml
```

- **pandas**: Ler e processa o arquivo CSV.  
- **lxml**: Analisa e manipula os arquivos XML, essencial para garantir a estrutura correta dos namespaces e das tags.

---

## 3. Estrutura de Arquivos
Para um funcionamento correto, todos os arquivos devem estar na mesma pasta:

```
/seu_projeto/
|-- csvToXML_metadata.py             # Este script
|-- Planilha_MGB2_Metadata_FIPE.csv  # Seu arquivo de dados
|-- tamplate_mgb20.xml               # Seu arquivo de modelo
```

---

## 4. Configuração do Script
Dentro do arquivo **csvToXML_metadata.py**, há uma seção de configuração no topo. Ajuste os nomes dos arquivos conforme necessário:

```python
# --- INÍCIO DA CONFIGURAÇÃO ---
caminho_csv = 'tb_mgb20_metadata.csv'
caminho_template_xml = 'tamplate_mgb20.xml'
pasta_saida = 'metadados_gerados'
# --- FIM DA CONFIGURAÇÃO ---
```

- **caminho_csv**: Nome do seu arquivo CSV de entrada.  
- **caminho_template_xml**: Nome do seu arquivo XML de template.  
- **pasta_saida**: Nome da pasta onde os arquivos XML gerados serão salvos. Esta pasta será criada automaticamente se não existir.

---

## 5. Formato dos Arquivos de Entrada

### 5.1. Arquivo CSV (tb_mgb20_metadata.csv)
Este arquivo é a fonte de todos os dados variáveis. Ele deve seguir regras estritas para que o script funcione corretamente:

- **Separador**: ponto e vírgula `;`  
- **Codificação**: UTF-8  
- **Cabeçalho**: A primeira linha deve conter os nomes exatos das colunas.  
- **Colunas não podem ter nomes duplicados. Devem ser numeradas sequencialmente, ex.:  
  - `MD_Keywords1`, `MD_Keywords2`, `MD_Keywords3`...  
- **Colunas de Datas (Formato ISO 8601)**:  
  - **dateStamp (Data do Metadado)**: em UTC (Zulu Time).  
    - Formato: `AAAA-MM-DDTHH:MM:SSZ`  
    - Exemplo: `2025-08-29T11:07:43Z`  
  - **date_creation (Data de Criação do Recurso)**: pode incluir fuso horário.  
    - Formato: `AAAA-MM-DDTHH:MM:SS-03:00`  
    - Exemplo: `2025-09-03T12:15:00-03:00` (São Paulo)

### 5.2. Arquivo de Template XML (tamplate_mgb20.xml)
- Deve ser um XML válido no padrão **MGB 2.0 BR**.  
- Precisa conter todas as tags que serão preenchidas, mesmo que vazias.  
  - Exemplo: `<gco:CharacterString></gco:CharacterString>`  
- Importante: O template deve conter a hierarquia correta das tags, incluindo:  
  - `<gmd:descriptiveKeywords>`  
  - Estrutura completa de datas (`gmd:date > gmd:CI_Date > gmd:date`).

---

## 6. Como Executar o Script

Abra um terminal ou prompt de comando, navegue até a pasta e execute:

```bash
python csvToXML_metadata.py
```

O script processará cada linha do CSV e informará no console cada XML gerado com sucesso.

---

## 7. Saída

O script criará uma pasta chamada **metadados_gerados** (ou o nome configurado em `pasta_saida`).  
Dentro dela, haverá **um XML para cada linha do CSV**.

Exemplo de nome de saída:  
```
metadado_0_Título_da_camada.xml
```

---

## 8. Detalhamento do Código (Como Funciona)

### Importação
O script utiliza as bibliotecas:
- `lxml`
- `pandas`
- `uuid`
- `datetime`

### Funções Auxiliares
- **set_element_text**: Preenche texto em tags de forma segura.  
- **set_element_attribute**: Define atributos sem quebrar o XML.  
- **atualizar_bloco_de_contato**: Atualiza informações de contato no XML.  

### Função Principal `gerar_metadados_xml`
1. **Validação**: Verifica se os arquivos de entrada existem.  
2. **Leitura do CSV**: Usa `pandas` para carregar os dados.  
3. **Loop Principal**: Itera linha a linha do CSV.  
4. **Análise do XML**: Recarrega o template em cada iteração, garantindo XML limpo.  
5. **Preenchimento**: Atualiza tags do XML com dados do CSV.  
6. **Lógica Específica**:  
   - **UUIDs**: Gera identificadores únicos (`fileIdentifier`, `uuid`).  
   - **Keywords**: Recria a estrutura `<gmd:MD_Keywords>` e preenche todas as palavras-chave.  
   - **Data de Criação**: Apaga e recria a hierarquia de datas (`<gco:DateTime>`).  
7. **Escrita**: Salva o XML em disco formatado (`pretty_print=True`).

---

Ajustar o CSV e o template XML para a sua necessidade.
