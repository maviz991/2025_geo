# v2.0 - Gerador de Metadados MGB 2.0 (csvToXML_metadata.py)

## 📌 Objetivo
Este script tem como finalidade **ler metadados a partir de um arquivo CSV**, preencher um **template XML** conforme os campos do CSV, e em seguida **armazenar o XML final em um banco PostgreSQL**.  
Os registros são armazenados em uma tabela específica, com suporte a **inserção e atualização automática** (`ON CONFLICT DO UPDATE`).

---

## ⚙️ Dependências

Antes de rodar o script, certifique-se de instalar as seguintes bibliotecas Python:

```bash
pip install lxml pandas psycopg2-binary
```

Bibliotecas utilizadas:
- **lxml** → Manipulação do XML.
- **pandas** → Leitura e tratamento do CSV.
- **uuid** → Geração de identificadores únicos (UUID).
- **datetime** → Controle de datas.
- **os** → Manipulação de arquivos.
- **psycopg2** → Conexão com PostgreSQL.

---

## 🗂 Estrutura de Arquivos

```
📂 projeto/
├── Planilha_MGB2_Metadata_FIPE.csv   # Planilha com os metadados de entrada
├── tamplate_mgb20.xml                # Template XML base
├── script.py                         # Script principal
└── README.md                         # Documentação
```

---

## 🛢 Configuração do Banco

A conexão ao banco é configurada no dicionário `db_config`:

```python
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

### Estrutura esperada da tabela

```sql
CREATE SCHEMA IF NOT EXISTS metadados;

CREATE TABLE metadados.registros (
    id UUID PRIMARY KEY,
    conteudo_xml XML NOT NULL
);
```

---

## 🔄 Fluxo de Execução

1. **Ler o CSV** (`Planilha_MGB2_Metadata_FIPE.csv`).  
   - Apenas registros com `LanguageCode` preenchido são processados.  
2. **Carregar o template XML** (`tamplate_mgb20.xml`).  
3. **Gerar UUID único** para cada registro.  
4. **Preencher os campos no XML** com os valores do CSV.  
5. **Converter o XML em string formatada**.  
6. **Inserir/atualizar no PostgreSQL**:  
   - Se o `id` já existir → atualiza (`conteudo_xml`).  
   - Se não existir → insere um novo registro.  
7. **Commit final** no banco.  

---

## ▶️ Como Rodar

```bash
python script.py
```

Certifique-se de:
- Ter o PostgreSQL rodando.
- Usuário e senha configurados corretamente no `db_config`.
- Arquivos CSV e XML estarem no mesmo diretório do script.

---

## 📤 Saída

- Para cada registro processado, será exibida uma mensagem no console:

```
Conectando ao banco 'seu_banco'...
Conexão bem-sucedida.
Encontrados 10 registros para processar.
--> Registro 'Título Exemplo' (ID: 123e4567-e89b-12d3-a456-426614174000) inserido/atualizado.
Todas as alterações foram salvas no banco.
Conexão fechada.
```

- Os registros ficam armazenados na tabela definida em `db_config`.

---

## 🛠 Tratamento de Erros

- **Arquivo CSV ou XML não encontrado** → O script interrompe e exibe mensagem de erro.  
- **Erro de banco de dados** → O `rollback()` é executado e a transação não é confirmada.  
- **Erro crítico** → O stack trace completo é mostrado para depuração.  

---

## 📌 Observações

- O script está pronto para trabalhar com **inserções incrementais**, evitando duplicação de registros.  
- Para ambientes de produção, recomenda-se:
  - Uso de variáveis de ambiente para credenciais (`os.environ`).  
  - Logging estruturado em vez de `print()`.  
  - Validação extra dos dados do CSV.  
