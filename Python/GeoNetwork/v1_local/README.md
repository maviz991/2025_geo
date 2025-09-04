# v1.0 - Gerador de Metadados MGB 2.0 (csvToXML_metadata.py)

## 1. Visão Geral
Este script automatiza a criação de múltiplos arquivos de metadados XML, seguindo o padrão **MGB 2.0 BR** (baseado na norma **ISO 19115**).  

Ele utiliza um arquivo CSV como fonte de dados e um arquivo XML como template estrutural.  
Para cada linha de dados no arquivo CSV, o script gera um novo arquivo XML, preenchendo os campos correspondentes do template.  

O script é projetado para ser robusto, garantindo que a estrutura do XML gerado seja válida e compatível com sistemas de gerenciamento de metadados, como o **GeoNetwork**.

---

## 2. Pré-requisitos
Antes de executar o script, certifique-se de que você tem:

- **Python 3.x** instalado.  
- As bibliotecas Python necessárias. Para instalá-las, abra seu terminal ou prompt de comando e execute:

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
|-- tb_mgb20_metadata.csv            # Seu arquivo de dados
|-- tamplate_mgb20.xml               # Seu arquivo de modelo
```

---

## 4. Configuração do Script
Dentro do arquivo `csvToXML_metadata.py`, há uma seção de configuração no topo.  
Você deve ajustar os nomes dos arquivos conforme necessário:

```python
# --- INÍCIO DA CONFIGURAÇÃO ---
caminho_csv = 'tb_mgb20_metadata.csv'
caminho_template_xml = 'tamplate_mgb20.xml'
pasta_saida = 'metadados_gerados'
# --- FIM DA CONFIGURAÇÃO ---
```

- **caminho_csv**: nome do seu arquivo CSV de entrada.  
- **caminho_template_xml**: nome do seu arquivo XML de template.  
- **pasta_saida**: nome da pasta onde os arquivos XML gerados serão salvos (será criada automaticamente se não existir).  

---

## 5. Formato dos Arquivos de Entrada

### 5.1. Arquivo CSV (tb_mgb20_metadata.csv)
Este arquivo é a fonte de todos os dados variáveis. Ele deve seguir regras estritas para que o script funcione corretamente:

- **Separador**: ponto e vírgula (`;`).  
- **Codificação**: UTF-8.  
- **Cabeçalho**: a primeira linha do arquivo deve conter os nomes exatos das colunas.  
- **Colunas não podem ter nomes duplicados**. Devem ser numeradas sequencialmente, ex.:
  - Exemplo: `MD_Keywords1`, `MD_Keywords2`, `MD_Keywords3`.  
- **Colunas de Datas (Formato ISO 8601)**:  
  - **dateStamp (Data do Metadado)**: em UTC (Zulu Time).  
    - Formato: `AAAA-MM-DDTHH:MM:SSZ`  
    - Exemplo: `2025-08-29T11:07:43Z`  
  - **date_creation (Data de Criação do Recurso)**: pode incluir o fuso horário.  
    - Formato: `AAAA-MM-DDTHH:MM:SS-03:00`  
    - Exemplo: `2025-09-03T12:15:00-03:00` (fuso de São Paulo).  

### 5.2. Arquivo de Template XML (tamplate_mgb20.xml)
Este arquivo serve como esqueleto para os metadados:

- Deve ser válido e estruturado de acordo com o padrão **MGB 2.0 BR**.  
- Deve conter todas as tags a serem preenchidas (mesmo vazias).  
  - Exemplo: `<gco:CharacterString></gco:CharacterString>`  
- Deve manter a hierarquia correta, incluindo:  
  - `<gmd:descriptiveKeywords>`  
  - Estrutura completa para a **data de criação**:  
    - `<gmd:date> → <gmd:CI_Date> → <gmd:date>`

---

## 6. Como Executar o Script
1. Abra um terminal ou prompt de comando.  
2. Navegue até a pasta onde os arquivos estão localizados.  
3. Execute o seguinte comando:

```bash
python csvToXML_metadata.py
```

O script processará cada linha do CSV e informará no console cada arquivo XML gerado com sucesso.

---

## 7. Saída
O script criará uma pasta chamada `metadados_gerados` (ou o nome definido em `pasta_saida`).  

Dentro dela, você encontrará um arquivo XML para cada linha do CSV.  
O nome de cada arquivo será gerado dinamicamente para ser único, combinando o índice da linha e o título do recurso.

**Exemplo:**
```
metadado_0_Título_da_camada.xml
```

---

## 8. Detalhamento do Código (Como Funciona)

### Importação
O script importa as bibliotecas:
- `lxml`  
- `pandas`  
- `uuid`  
- `datetime`

### Funções Auxiliares
- `set_element_text`  
- `set_element_attribute`  
- `atualizar_bloco_de_contato`  

Essas funções evitam que o script quebre caso uma tag específica não seja encontrada no template. Também ajudam a manter o código limpo e organizado.

### Função Principal: `gerar_metadados_xml`
1. **Validação**: verifica se os arquivos de entrada existem.  
2. **Leitura do CSV**: carrega os dados usando pandas, tratando linhas vazias.  
3. **Loop Principal**:  
   - Itera sobre cada linha do CSV.  
   - Recarrega o template XML a cada iteração (`lxml.etree.parse`).  
   - Preenche as tags com os dados da linha.  
4. **Lógica Específica**:  
   - **UUIDs**: novos identificadores únicos para `fileIdentifier` e `uuid` do autor.  
   - **Keywords**: recria `<gmd:MD_Keywords>` e adiciona todas as palavras-chave corretamente.  
   - **Data de Criação**: recria a estrutura `<gmd:date>` com `<gco:DateTime>` baseado no CSV.  
5. **Escrita do Arquivo**: salva o XML gerado com `tree.write()`, preservando os namespaces e com indentação (`pretty_print=True`).  

---
## 9. Saída
O script cria arquivos. A saída são registros inseridos/atualizados no diretorio local de saída `pasta_saida = 'metadados_gerados'`.

---

## 10. 🚨 Pontos de Atenção e Limitações 
Esta seção detalha as suposições do script. O seu bom funcionamento depende do alinhamento entre os dados de entrada e a configuração.

### 10.1. Leitura do Arquivo CSV
- **Separador Fixo**: O script espera que o CSV use ponto e vírgula (`sep=';'`). Para usar outro separador (ex: vírgula), altere este parâmetro na linha `pd.read_csv()`.
- **Validação de Dados**: O script assume que os dados no CSV estão limpos e no formato correto.
  - Ele remove linhas onde a coluna `LanguageCode` está vazia, mas não valida a presença de outras colunas obrigatórias.
  - Valores não-numéricos em colunas como `spatialResolution_denominator` ou coordenadas geográficas causarão um erro. É crucial garantir a qualidade dos dados antes da execução.

### 10.2. Template XML
- **Estrutura e Namespaces**: A execução depende de um template XML bem formado e que use os prefixos de namespace esperados (`gmd`, `gco`, etc.). Se uma tag ou namespace esperado não existir, a busca por XPath falhará silenciosamente, e o campo correspondente não será preenchido.

### 10.3. Banco de Dados
- **Credenciais e Permissões**: As credenciais em `db_config` devem ser preenchidas corretamente. O usuário do banco precisa de permissões de `INSERT` e `UPDATE` na tabela `metadata`.
- **Estrutura da Tabela**: A lógica `ON CONFLICT (uuid)` assume que a coluna `uuid` na tabela `metadata` possui uma restrição `UNIQUE` ou é a `PRIMARY KEY`. Esta é a configuração padrão do GeoNetwork.

### 10.4. Lógica de Execução
- **UUID e Re-execução**: O `fileIdentifier` (UUID) é gerado pelo script para cada linha do CSV, garantindo que seja único. A cláusula `ON CONFLICT` foi projetada para o caso de você **re-executar o script** com o mesmo CSV (ou um CSV que gere UUIDs já existentes); ela permite **atualizar** registros em vez de falhar.
- **Atualização de Contatos**: O script procura por um bloco de contato com o papel (`role`) de `author` e para no primeiro que encontra (`break`). Ele assume que há apenas um contato desse tipo a ser atualizado.
- **Logging**: O script usa `print()` para feedback. Para ambientes de produção ou depuração complexa, a implementação de um sistema de logging (como a biblioteca `logging` do Python) é uma melhoria recomendada.
