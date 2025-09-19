#Use a lista de fileID gerada por footprints_search.py
import asf_search as asf
from getpass import getpass
import os
import zipfile
import shutil

# --- CONFIGURAÇÕES ---
download_path = 'temp_downloads'
dem_path = 'dems_finais_sp'
granule_list_file = 'list_img.txt'

os.makedirs(download_path, exist_ok=True)
os.makedirs(dem_path, exist_ok=True)

print(f"Zips temporários serão baixados em: {os.path.abspath(download_path)}")
print(f"DEMs finais serão salvos em: {os.path.abspath(dem_path)}")

try:
    print(f"\nLendo a lista de imagens do arquivo '{granule_list_file}'...")
    with open(granule_list_file, 'r') as f:
        lista_de_granulos = [line.strip() for line in f if line.strip()]
    
    if not lista_de_granulos:
        raise ValueError("O arquivo 'list_img.txt' está vazio ou não foi encontrado.")
        
    print(f"{len(lista_de_granulos)} imagens serão processadas.")

    # --- AUTENTICAÇÃO ---
    session = asf.ASFSession()
    username = input("Digite seu usuário do NASA Earthdata: ")
    password = getpass("Digite sua senha do NASA Earthdata: ")
    session.auth_with_creds(username, password)
    print("Auticação realizada com sucesso!")

    # --- BUSCA ---
    print("\nIniciando a busca pelos produtos da sua lista...")
    results = asf.granule_search(lista_de_granulos)
    total_files = len(results)
    print(f"Busca concluída. {total_files} produtos correspondentes encontrados.")

    if total_files > 0:
        print("\nIniciando o processo de download e extração...")

        for index, product in enumerate(results):
            zip_filename = product.properties['fileName']
            zip_filepath = os.path.join(download_path, zip_filename)
            
            print(f"\n({index + 1}/{total_files}) Processando: {zip_filename}")

            try:
                print(f"    - Baixando zip...")
                product.download(path=download_path, session=session)
                
                print(f"    - Procurando por DEM no zip...")
                with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
                    dem_files = [
                        name for name in zip_ref.namelist() 
                        if name.lower().endswith('_dem.tif') or name.lower().endswith('.dem.tif')
                    ]
                  
                    if dem_files:
                        full_dem_path_in_zip = dem_files[0]
                        dem_basename = os.path.basename(full_dem_path_in_zip)
                        dest_filepath = os.path.join(dem_path, dem_basename)
                        
                        print(f"    - DEM encontrado: '{full_dem_path_in_zip}'. Extraindo...")
                        
                        with zip_ref.open(full_dem_path_in_zip) as source_file:
                            with open(dest_filepath, 'wb') as dest_file:
                                shutil.copyfileobj(source_file, dest_file)
                        
                        print(f"   ✅ - DEM salvo com sucesso!")
                    else:
                        print(f"    - AVISO: Nenhum arquivo DEM (_dem.tif ou .dem.tif) encontrado neste zip.")
                        print(f"    - Conteúdo do zip: {zip_ref.namelist()}")

            except Exception as e:
                print(f"   ❌ - ERRO ao processar o arquivo {zip_filename}: {e}")
            
            finally:
                if os.path.exists(zip_filepath):
                    print(f"    - Deletando zip para liberar espaço...")
                    os.remove(zip_filepath)
        
        print("\n\n 🆗 Processo concluído!")

except Exception as e:
    print(f"\nOcorreu um erro inesperado: {e}")
