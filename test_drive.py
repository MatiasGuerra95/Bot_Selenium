from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def test_drive_connection():
    try:
        creds = Credentials.from_service_account_file(
            "service_account.json",
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        drive_service = build("drive", "v3", credentials=creds)
        print("Conexión con Google Drive establecida con éxito.")

        results = drive_service.files().list(
            pageSize=10,
            fields="files(id, name)"
        ).execute()
        items = results.get("files", [])

        if not items:
            print("No se encontraron archivos en Google Drive.")
        else:
            print("Archivos encontrados en Google Drive:")
            for idx, item in enumerate(items, start=1):
                print(f"{idx}. {item['name']} (ID: {item['id']})")
    except Exception as e:
        print(f"Error al conectar con Google Drive: {e}")

if __name__ == "__main__":
    test_drive_connection()
