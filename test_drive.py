from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def test_drive():
    # Carga las credenciales
    creds = Credentials.from_service_account_file("service_account.json",
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    # Construye el servicio de Drive
    service = build("drive", "v3", credentials=creds)
    
    # Lista los primeros 10 archivos del Drive
    results = service.files().list(
        pageSize=10, fields="files(id, name)"
    ).execute()
    items = results.get('files', [])
    if not items:
        print('No se encontraron archivos.')
    else:
        print('Archivos:')
        for item in items:
            print(f"{item['name']} ({item['id']})")

test_drive()
