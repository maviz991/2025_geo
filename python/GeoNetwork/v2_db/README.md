# v2.0 - Gerador e Inseridor de Metadados MGB 2.0 (csvToXmlToDB.py)

## 1. Visão Geral
Este script representa uma evolução do gerador de metadados, automatizando não apenas a criação dos arquivos XML no padrão **MGB 2.0 BR** (baseado na norma **ISO 19115**), mas também a sua **inserção/atualização direta** em um banco de dados **PostgreSQL**.

Ele utiliza um arquivo CSV como fonte de dados e um XML como template. Para cada linha no CSV, o script gera o conteúdo XML correspondente e o armazena na base de dados, eliminando a necessidade de gerenciar arquivos físicos.

Essa abordagem centraliza o gerenciamento dos metadados e torna o script re-executável, atualizando registros existentes caso sejam processados novamente, graças à lógica "UPSERT" (Update/Insert).

---

## 2. Pré-requisitos
Antes de executar o script, certifique-se de que você tem:

- **Python 3.x** instalado.
- **Acesso a um banco de dados PostgreSQL**.
- As bibliotecas Python necessárias. Para instalá-las, abra seu terminal ou prompt de comando e execute:

```bash
pip install pandas lxml psycopg2-binary
```

- **pandas**: Para ler e processar o arquivo CSV.
- **lxml**: Para analisar e manipular os arquivos XML.
- **psycopg2-binary**: O driver de conexão para interagir com o banco de dados PostgreSQL.

---

## 3. Estrutura de Arquivos
Os arquivos de entrada devem estar na mesma pasta que o script:

```
/seu_projeto/
|-- csvToXmlToDB.py                  # Este script
|-- tb_mgb20_metadata.csv            # Seu arquivo de dados
|-- tamplate_mgb20.xml               # Seu arquivo de modelo
```

---

## 4. Configuração do Script
Dentro do script, existem duas seções de configuração que devem ser ajustadas:

### 4.1. Configuração dos Arquivos
```python
# --- CONFIGURAÇÃO DOS ARQUIVOS ---
caminho_csv = 'tb_mgb20_metadata.csv'
caminho_template_xml = 'tamplate_mgb20.xml'
```

### 4.2. Configuração do Banco de Dados
Esta seção é crucial e deve ser preenchida com as informações do seu ambiente.

```python
# --- CONFIGURAÇÃO DO BANCO ---
db_config = {
    "host": "localhost",
    "port": "5432",
    "dbname": "seu_banco",
    "user": "seu_usuario",
    "password": "sua_senha",
    "schema": "metadados",
    "table": "registros",
    "id_column": "id",
    "xml_column": "conteudo_xml"
}
```
- **host, port, dbname, user, password**: credenciais de acesso ao seu PostgreSQL.
- **schema**: o schema onde a tabela de metadados está localizada (ex: `public`).
- **table**: o nome da tabela que armazenará os metadados.
- **id_column**: o nome da coluna que servirá como chave primária (armazenará o `fileIdentifier`).
- **xml_column**: o nome da coluna que armazenará o conteúdo XML completo.

---

## 5. Preparação do Banco de Dados
Antes da primeira execução, a tabela de destino precisa existir no banco. Você pode criá-la com um comando SQL semelhante a este:

```sql
-- Garante que o schema exista (opcional, mas recomendado)
CREATE SCHEMA IF NOT EXISTS metadados;

-- Cria a tabela para armazenar os registros de metadados
CREATE TABLE metadados.registros (
    id VARCHAR(255) PRIMARY KEY,
    conteudo_xml TEXT,
    data_atualizacao TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```
**Importante:** a coluna `id` (ou o nome que você definir em `id_column`) **deve ser a chave primária** (`PRIMARY KEY`) para que a lógica de atualização (`ON CONFLICT`) do script funcione corretamente.

---

## 6. Formato dos Arquivos de Entrada

### 6.1. Arquivo CSV (tb_mgb20_metadata.csv)
As regras para o arquivo CSV permanecem as mesmas: separador por ponto e vírgula, codificação UTF-8, cabeçalho na primeira linha e nomes de coluna únicos (ex: `MD_Keywords1`, `MD_Keywords2`). Os formatos de data ISO 8601 são essenciais.

### 6.2. Arquivo de Template XML (tamplate_mgb20.xml)
O arquivo de template deve ser um XML válido no padrão MGB 2.0 BR, contendo todas as tags estruturais necessárias para o preenchimento.

---

## 7. Como Executar o Script
1.  Abra um terminal ou prompt de comando.
2.  Navegue até a pasta onde os arquivos estão localizados.
3.  Execute o seguinte comando:

```bash
python csvToXmlToDB.py
```

O script se conectará ao banco, processará cada linha do CSV e informará no console cada registro que for inserido ou atualizado na base de dados.

---

## 8. Saída
O script **não cria arquivos XML locais**. A saída do processo são registros no banco de dados:

- Para cada linha do CSV, uma linha correspondente será **inserida** ou **atualizada** na tabela configurada.
- A coluna `id_column` será preenchida com o `fileIdentifier` (UUID) gerado para o metadado.
- A coluna `xml_column` conterá o texto completo do metadado XML gerado.

---

## 9. Detalhamento do Código (Como Funciona)

### Função Principal: `gerar_e_inserir_metadados`
1.  **Conexão com o Banco**: estabelece uma conexão com o PostgreSQL usando `psycopg2.connect()`.
2.  **Leitura do CSV**: carrega os dados usando pandas.
3.  **Loop Principal**:
    - Itera sobre cada linha do CSV.
    - Recarrega o template XML a cada iteração.
    - Preenche as tags com os dados da linha, gerando novos UUIDs para o registro e o autor.
    - Converte a árvore XML final para uma string de texto codificada em UTF-8.
4.  **Inserção no Banco (Lógica "UPSERT")**:
    - O script utiliza o comando `INSERT ... ON CONFLICT ... DO UPDATE`.
    - **Se o `id` (fileIdentifier) não existir na tabela**, ele insere um novo registro.
    - **Se o `id` já existir**, em vez de dar erro, ele atualiza o `conteudo_xml` da linha existente com a nova versão. Isso torna o script seguro para ser re-executado.
5.  **Gerenciamento da Transação**:
    - `conn.commit()`: salva todas as inserções/atualizações no banco ao final do processo.
    - `conn.rollback()`: em caso de erro, desfaz qualquer alteração parcial para manter a consistência dos dados.
    - O bloco `finally` garante que a conexão com o banco seja sempre fechada de forma segura, mesmo se ocorrerem erros.
  
---
