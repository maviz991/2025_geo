# Matheus Dias de Aviz 
# Transforma dados em tabelas em um tamplate XML (Perfil MGB 2.0) e insere em um banco de dados PostgreSQL
from lxml import etree as ET
import pandas as pd
import uuid
from datetime import datetime, timezone
import os
import psycopg2 # Biblioteca para conectar com o PostgreSQL

# --- CONFIGURAÇÃO DOS ARQUIVOS DE ENTRADA ---
caminho_csv = 'tb_mgb2_metadata.csv' # Corrigi o nome para .csv
caminho_template_xml = 'tamplate_mgb20.xml'

# --- CONFIGURAÇÃO GENÉRICA DO BANCO DE DADOS POSTGRESQL ---
db_config = {
    "host": "localhost",
    "port": "5432",
    "dbname": "seu_banco",
    "user": "seu_usuario",
    "password": "sua_senha",
    "schema": "metadados",      # Schema onde a tabela está
    "table": "registros",       # Nome da tabela de destino
    "id_column": "id",          # Nome da coluna para o UUID
    "xml_column": "conteudo_xml"  # Nome da coluna para o XML
}

def set_element_text(parent_element, xpath, text_value, ns_map):
    element = parent_element.find(xpath, namespaces=ns_map)
    if element is not None:
        element.text = text_value

def set_element_attribute(parent_element, xpath, attr_name, attr_value, ns_map):
    element = parent_element.find(xpath, namespaces=ns_map)
    if element is not None:
        element.set(attr_name, attr_value)

def atualizar_bloco_de_contato(contato_node, csv_row, ns_map):
    if contato_node is None: return
    contato_node.set('uuid', str(uuid.uuid4()))
    set_element_text(contato_node, './/gmd:individualName/gco:CharacterString', csv_row.get('contact_individualName'), ns_map)
    set_element_text(contato_node, './/gmd:organisationName/gco:CharacterString', csv_row.get('contact_organisationName'), ns_map)
    set_element_text(contato_node, './/gmd:positionName/gco:CharacterString', csv_row.get('contact_positionName'), ns_map)
    set_element_text(contato_node, './/gmd:contactInfo//gmd:voice/gco:CharacterString', csv_row.get('contact_phone'), ns_map)
    set_element_text(contato_node, './/gmd:contactInfo//gmd:deliveryPoint/gco:CharacterString', csv_row.get('contact_deliveryPoint'), ns_map)
    set_element_text(contato_node, './/gmd:contactInfo//gmd:city/gco:CharacterString', csv_row.get('contact_city'), ns_map)
    set_element_text(contato_node, './/gmd:contactInfo//gmd:administrativeArea/gco:CharacterString', csv_row.get('contact_administrativeArea'), ns_map)
    set_element_text(contato_node, './/gmd:contactInfo//gmd:postalCode/gco:CharacterString', str(csv_row.get('contact_postalCode', '')), ns_map)
    set_element_text(contato_node, './/gmd:contactInfo//gmd:country/gco:CharacterString', csv_row.get('contact_country'), ns_map)
    set_element_text(contato_node, './/gmd:contactInfo//gmd:electronicMailAddress/gco:CharacterString', csv_row.get('contact_email'), ns_map)

# --- Função principal para inserir no banco de dados ---
def gerar_e_inserir_metadados(csv_path, template_path, db_params_config):
    if not os.path.exists(csv_path):
        print(f"Erro: Arquivo CSV não encontrado em '{csv_path}'")
        return
    if not os.path.exists(template_path):
        print(f"Erro: Template XML não encontrado em '{template_path}'")
        return

    conn = None
    try:
        # Extrai parâmetros de conexão do dicionário principal
        db_connect_params = {
            "host": db_params_config["host"],
            "port": db_params_config["port"],
            "dbname": db_params_config["dbname"],
            "user": db_params_config["user"],
            "password": db_params_config["password"],
        }
        
        # Conecta ao banco de dados
        print(f"Conectando ao banco de dados '{db_params_config['dbname']}'...")
        conn = psycopg2.connect(**db_connect_params)
        cursor = conn.cursor()
        print("Conexão bem-sucedida.")

        df = pd.read_csv(csv_path, sep=';', header=0, dtype=str).fillna('')
        df = df.loc[df['LanguageCode'] != '']
        print(f"Encontrados {len(df)} registros para processar.")

        for index, row in df.iterrows():
            parser = ET.XMLParser(remove_blank_text=True)
            tree = ET.parse(template_path, parser)
            root = tree.getroot()
            ns = root.nsmap
            
            # Gera o UUID e o insere no XML
            file_identifier = str(uuid.uuid4())
            set_element_text(root, './gmd:fileIdentifier/gco:CharacterString', file_identifier, ns)
            
            # Preenche o resto do XML com a lógica já validada
            set_element_text(root, './gmd:dateStamp/gco:DateTime', row.get('dateStamp'), ns)
            set_element_attribute(root, './gmd:language/gmd:LanguageCode', 'codeListValue', row.get('LanguageCode'), ns)
            set_element_attribute(root, './gmd:characterSet/gmd:MD_CharacterSetCode', 'codeListValue', row.get('characterSet'), ns)
            set_element_attribute(root, './gmd:hierarchyLevel/gmd:MD_ScopeCode', 'codeListValue', row.get('hierarchyLevel'), ns)
            
            for party in root.findall('./gmd:contact/gmd:CI_ResponsibleParty', namespaces=ns):
                if party.find('.//gmd:role/gmd:CI_RoleCode', namespaces=ns).get('codeListValue') == 'author':
                    atualizar_bloco_de_contato(party, row, ns)
                    break
            
            id_info = root.find('.//gmd:identificationInfo/gmd:MD_DataIdentification', namespaces=ns)
            if id_info is not None:
                for party in id_info.findall('./gmd:pointOfContact/gmd:CI_ResponsibleParty', namespaces=ns):
                    if party.find('.//gmd:role/gmd:CI_RoleCode', namespaces=ns).get('codeListValue') == 'author':
                        atualizar_bloco_de_contato(party, row, ns)
                        break

                set_element_text(id_info, './/gmd:citation//gmd:title/gco:CharacterString', row.get('title'), ns)
                
                # Lógica "Destruir e Reconstruir" para a data de criação
                date_parent = id_info.find('.//gmd:citation//gmd:date/gmd:CI_Date/gmd:date', namespaces=ns)
                if date_parent is not None:
                    date_parent.clear()
                    date_time_element = ET.SubElement(date_parent, f"{{{ns['gco']}}}DateTime")
                    date_time_element.text = row.get('date_creation', '')
                
                set_element_text(id_info, './gmd:abstract/gco:CharacterString', row.get('abstract'), ns)
                set_element_attribute(id_info, './gmd:status/gmd:MD_ProgressCode', 'codeListValue', row.get('status_codeListValue'), ns)
                set_element_attribute(id_info, './gmd:language/gmd:LanguageCode', 'codeListValue', row.get('LanguageCode'), ns)
                set_element_attribute(id_info, './gmd:characterSet/gmd:MD_CharacterSetCode', 'codeListValue', row.get('characterSet'), ns)
                
                keyword_container = id_info.find('./gmd:descriptiveKeywords', namespaces=ns)
                if keyword_container is not None:
                    keyword_container.clear()
                    md_keywords_node = ET.SubElement(keyword_container, f"{{{ns['gmd']}}}MD_Keywords")
                    keywords_found = False
                    for col in ['MD_Keywords1', 'MD_Keywords2', 'MD_Keywords3', 'MD_Keywords4']:
                        if col in row and row[col]:
                            keywords_found = True
                            keyword_node = ET.SubElement(md_keywords_node, f"{{{ns['gmd']}}}keyword")
                            char_string = ET.SubElement(keyword_node, f"{{{ns['gco']}}}CharacterString")
                            char_string.text = row[col]
                    if not keywords_found:
                        keyword_container.remove(md_keywords_node)

                set_element_attribute(id_info, './/gmd:spatialRepresentationType/gmd:MD_SpatialRepresentationTypeCode', 'codeListValue', row.get('MD_SpatialRepresentationTypeCode_codeListValue'), ns)
                set_element_text(id_info, './/gmd:spatialResolution//gmd:denominator/gco:Integer', str(int(float(row.get('spatialResolution_denominator', 0)))), ns)
                set_element_text(id_info, './/gmd:topicCategory/gmd:MD_TopicCategoryCode', row.get('topicCategory'), ns)
                set_element_text(id_info, './/gmd:extent//gmd:westBoundLongitude/gco:Decimal', str(row.get('westBoundLongitude')), ns)
                set_element_text(id_info, './/gmd:extent//gmd:eastBoundLongitude/gco:Decimal', str(row.get('eastBoundLongitude')), ns)
                set_element_text(id_info, './/gmd:extent//gmd:southBoundLatitude/gco:Decimal', str(row.get('southBoundLatitude')), ns)
                set_element_text(id_info, './/gmd:extent//gmd:northBoundLatitude/gco:Decimal', str(row.get('northBoundLatitude')), ns)

            # Converte o XML gerado para uma string
            xml_string_output = ET.tostring(root, pretty_print=True, xml_declaration=True, encoding='utf-8').decode('utf-8')

            # Query
            query = f"""
                INSERT INTO {db_params_config['schema']}.{db_params_config['table']} 
                ({db_params_config['id_column']}, {db_params_config['xml_column']}) 
                VALUES (%s, %s)
                ON CONFLICT ({db_params_config['id_column']}) DO UPDATE SET
                {db_params_config['xml_column']} = EXCLUDED.{db_params_config['xml_column']};
            """
            
            # Executa a query
            cursor.execute(query, (file_identifier, xml_string_output))
            print(f"--> Registro '{row.get('title')}' (ID: {file_identifier}) inserido/atualizado no banco.")

        # Salva (commita) todas as transações no banco de dados
        conn.commit()
        print("\nTodas as alterações foram salvas no banco de dados.")

    except psycopg2.Error as e:
        print(f"\nERRO DE BANCO DE DADOS: {e}")
        if conn:
            conn.rollback() # Desfaz as alterações da transação em caso de erro
    except Exception as e:
        print(f"\nERRO CRÍTICO: Ocorreu um erro inesperado: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Garante que a conexão seja sempre fechada
        if conn:
            cursor.close()
            conn.close()
            print("Conexão com o banco de dados foi fechada.")

if __name__ == "__main__":
    gerar_e_inserir_metadados(caminho_csv, caminho_template_xml, db_config)
