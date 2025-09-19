#Excute em um terminal python
import ee

try:
    # Esta primeira tentativa vai falhar porque as credenciais ainda não existem.
    ee.Initialize()

except Exception as e:
    print("Primeira autenticação necessária...")
    
    # Usando o auth_mode que a documentação sugere
    # Isso forçará o método de autenticação interativo (baseado em link).
    ee.Authenticate(auth_mode='notebook')
    
    # Depois da autenticação bem-sucedida, inicializar de novo.
    ee.Initialize()

print("Conexão com o Google Earth Engine estabelecida com sucesso!")


# --------------------------------------------------------------------------
# PASSO 2: DEFINIR A ÁREA DE INTERESSE
aoi_sp = ee.Geometry.Rectangle([-53.2, -25.4, -44.1, -19.7])

# PASSO 3: PROCESSAMENTO (LÓGICA CORRETA)
# 1. Carrega a ImageCollection com o ID correto e filtra pela nossa área
dem_collection = ee.ImageCollection('COPERNICUS/DEM/GLO30').filterBounds(aoi_sp)

# 2. Seleciona a banda com o nome correto ('DEM')
dem_band = dem_collection.select('DEM')

# 3. Usa .median() para criar a imagem final e corta para a área de interesse
dem_sp = dem_band.median().clip(aoi_sp)

print("Processamento em nuvem concluído. O DEM de São Paulo está pronto para ser processado.")

# --------------------------------------------------------------------------
# PASSO 4: EXPORTAR O RESULTADO FINAL
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

task.start()

print("\nExportação iniciada com sucesso!")
print("Acesse a aba 'Tasks' no GEE Code Editor para acompanhar:")
print("https://code.earthengine.google.com/tasks")
print(f"ID da tarefa: {task.id} | Status inicial: {task.status()['state']}")
