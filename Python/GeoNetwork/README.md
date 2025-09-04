# Gerador de Metadados MGB 2.0 (csvToXML_metadata.py)

## 1. Visão Geral
Este script automatiza a criação de múltiplos arquivos de metadados XML, seguindo o padrão **MGB 2.0 BR** (baseado na norma **ISO 19115**).  

Ele utiliza um arquivo CSV como fonte de dados e um arquivo XML como template estrutural.  
Para cada linha de dados no arquivo CSV, o script gera um novo arquivo XML, preenchendo os campos correspondentes do template.  

O script é projetado para ser robusto, garantindo que a estrutura do XML gerado seja válida e compatível com sistemas de gerenciamento de metadados, como o **GeoNetwork**.

► A Versão 1 tem sáida em um CSV local;

► A Versão 2 tem INSERT/UPDATE em um banco PostegreSQL.
