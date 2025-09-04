# v2.1 - Gerador e Inseridor de Metadados para GeoNetwork (csvToXmlToDB.py)

## 1. Visão Geral
Este script automatiza a criação de registros de metadados no padrão **MGB 2.0 BR** (ISO 19115) e os insere/atualiza diretamente na tabela nativa do **GeoNetwork**, o sistema de gerenciamento de metadados.

A principal vantagem é a capacidade de realizar a carga e atualização em massa de registros a partir de uma planilha CSV, integrando-se diretamente ao banco de dados PostgreSQL do GeoNetwork.

**⚠️ Importante**: Esta abordagem manipula diretamente o banco de dados do GeoNetwork. Ela bypassa as APIs da aplicação, o que exige configuração cuidadosa. Recomendo que sejam feitos exaustivos testes em DEV!

---

## 2. Pré-requisitos
- **Python 3.x** instalado.
- **Acesso de escrita** ao banco de dados PostgreSQL do GeoNetwork.
- Bibliotecas Python:
```bash
pip install pandas lxml psycopg2-binary
```

---

## 3. Estrutura de Arquivos
```
/seu_projeto/
|-- csvToXmlToDB.py                  # Este script
|-- tb_mgb20_metadata.csv            # Seu arquivo de dados
|-- tamplate_mgb20.xml               # Seu arquivo de modelo
```

---

## 4. Configuração do Script

### 4.1. Configuração dos Arquivos
```python
# --- CONFIGURAÇÃO DOS ARQUIVOS ---
caminho_csv = 'tb_mgb20_metadata.csv'
caminho_template_xml = 'tamplate_mgb20.xml'
```

### 4.2. Configuração do Banco de Dados (Exemplo para GeoNetwork)
Esta seção deve ser preenchida com os dados da sua instalação do GeoNetwork. Os valores abaixo são os padrões mais comuns.

```python
# --- CONFIGURAÇÃO DO BANCO ---
db_config = {
    "host": "localhost",
    "port": "5432",
    "dbname": "geonetwork",      # Nome padrão do banco do GeoNetwork
    "user": "geonetwork",       # Usuário padrão
    "password": "sua_senha",    # SENHA DO USUÁRIO DO BANCO
    "schema": "public",         # Schema padrão
    "table": "metadata",        # Tabela nativa de metadados
    "id_column": "uuid",        # Coluna do UUID ( NÃO É 'id' )
    "xml_column": "data"        # Coluna do XML ( NÃO É 'conteudo_xml' )
}
```

---

## 5. Entendendo a Tabela do GeoNetwork
O script **não cria uma tabela nova**. Ele interage com a tabela `metadata` que já existe na sua instalação do GeoNetwork. As colunas mais importantes são:

- **id (integer)**: Chave primária interna, auto-incrementada. O script **não deve** inserir valores aqui.
- **uuid (varchar)**: O identificador único do metadado (`fileIdentifier`). É a chave que o nosso script usará para `INSERT` e `UPDATE`.
- **data (text ou xml)**: Armazena o conteúdo completo do arquivo XML.
- **schemaId (varchar)**: Identifica o padrão do metadado. Para o MGB 2.0, o valor deve ser `iso19139`.
- **owner (integer)**: O ID do usuário dono do metadado. Por padrão, o usuário `admin` tem ID `2`.
- **doctype (varchar)**: Define o tipo de documento. Geralmente `METADATA`.

Para que o GeoNetwork reconheça os registros, o script precisa preencher esses campos essenciais.

---

## 6. Query SQL
A query `INSERT` padrão do script precisa ser modificada para incluir os campos obrigatórios do GeoNetwork. Localize a variável `query` dentro da função `gerar_e_inserir_metadados` e substitua-a pela seguinte:

```python
# Query adaptada para a tabela 'metadata' do GeoNetwork
query = f"""
    INSERT INTO {db_params['schema']}.{db_params['table']} 
        (uuid, data, owner, doctype, schemaid) 
    VALUES 
        (%s, %s, 2, 'METADATA', 'iso19139')
    ON CONFLICT (uuid) DO UPDATE 
        SET data = EXCLUDED.data;
"""
# Na linha do cursor.execute, passe apenas os dois valores necessários
cursor.execute(query, (file_identifier, xml_string_output))
```
**O que essa query faz:**
- Insere o `uuid` e o `data` (XML) a partir dos dados gerados.
- Define valores fixos para os outros campos:
  - `owner = 2` (usuário admin)
  - `doctype = 'METADATA'`
  - `schemaid = 'iso19139'`
- Se um metadado com o mesmo `uuid` já existir, ele apenas atualiza o conteúdo XML (`data`).

---

## 7. Como Executar o Script
1.  Configure os dados do banco e ajuste a query SQL conforme as seções 4 e 6.
2.  Abra um terminal na pasta do projeto.
3.  Execute o comando:
```bash
python csvToXmlToDB.py
```

---

## 8. Pós-Execução: Reindexação no GeoNetwork
**⚠️ ALERTA**

A inserção direta no banco de dados **NÃO ATUALIZA OS ÍNDICES DE BUSCA** do GeoNetwork. Após executar o script, os metadados estarão na tabela, mas **não aparecerão nos resultados de busca**.

Para que eles apareçam, você precisa forçar uma reindexação:
1.  Acesse a interface do GeoNetwork como administrador.
2.  Vá para **Admin console > Ferramentas > Reindex records**.
3.  Clique no botão **Rebuild index**.

Este passo é **obrigatório** para que o GeoNetwork "descubra" os novos registros inseridos diretamente no banco.

---
