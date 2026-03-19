from __future__ import print_function
import os.path
import csv
from datetime import datetime, timedelta
import io

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

ARCHIVO = "horas_practicas.csv"
TEMP_ENTRADA = "entrada.tmp"

SCOPES = ['https://www.googleapis.com/auth/drive.file']

# PON AQUÍ EL ID DE TU ARCHIVO DE GOOGLE DRIVE
FILE_ID = "AQUI_TU_ID"

# ---------------- GOOGLE DRIVE ---------------- #

def autenticar():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def descargar_csv(service):
    request = service.files().get_media(fileId=FILE_ID)
    fh = io.FileIO(ARCHIVO, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    print("CSV descargado desde Google Drive.")

def subir_csv(service):
    media = MediaFileUpload(ARCHIVO, mimetype='text/csv')
    service.files().update(
        fileId=FILE_ID,
        media_body=media
    ).execute()
    print("CSV actualizado en Google Drive.")

# ---------------- TU CÓDIGO ORIGINAL ---------------- #

def calcular_horas(inicio, fin):
    formato = "%H:%M"
    h_inicio = datetime.strptime(inicio, formato)
    h_fin = datetime.strptime(fin, formato)

    if h_fin < h_inicio:
        h_fin += timedelta(days=1)

    return h_fin - h_inicio

def inicializar_csv():
    if not os.path.exists(ARCHIVO):
        with open(ARCHIVO, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["fecha", "entrada", "salida", "horas"])

def registrar_entrada():
    ahora = datetime.now()
    hora = ahora.strftime("%H:%M")
    fecha = ahora.strftime("%Y-%m-%d")

    with open(TEMP_ENTRADA, "w") as f:
        f.write(f"{fecha},{hora}")

    print(f"Entrada registrada automáticamente: {fecha} a las {hora}")

def registrar_salida():
    if not os.path.exists(TEMP_ENTRADA):
        print("No hay una entrada registrada. Registra primero la hora de entrada.")
        return

    ahora = datetime.now()
    salida = ahora.strftime("%H:%M")

    with open(TEMP_ENTRADA, "r") as f:
        contenido = f.read().strip()

    fecha, entrada = contenido.split(",")

    total = calcular_horas(entrada, salida)

    with open(ARCHIVO, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([fecha, entrada, salida, str(total)])

    os.remove(TEMP_ENTRADA)

    print(f"Salida registrada automáticamente: {salida}")
    print(f"Jornada completa: {entrada} - {salida} → {total}")

def registrar_manual():
    fecha = input("Fecha (YYYY-MM-DD): ")
    entrada = input("Hora de entrada (HH:MM): ")
    salida = input("Hora de salida (HH:MM): ")

    total = calcular_horas(entrada, salida)

    with open(ARCHIVO, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([fecha, entrada, salida, str(total)])

    print(f"Jornada manual registrada: {entrada} - {salida} → {total}")

def mostrar_total():
    total_general = timedelta()

    with open(ARCHIVO, newline="", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        for fila in lector:
            h = fila["horas"]
            h_dt = datetime.strptime(h, "%H:%M:%S")
            total_general += timedelta(
                hours=h_dt.hour,
                minutes=h_dt.minute,
                seconds=h_dt.second
            )

    horas_decimales = total_general.total_seconds() / 3600
    print(f"\nTotal acumulado: {total_general} ({horas_decimales:.2f} horas decimales)")

def eliminar_jornada():
    fecha = input("Introduce la fecha a eliminar (YYYY-MM-DD): ")

    filas_nuevas = []
    eliminado = False

    with open(ARCHIVO, newline="", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        for fila in lector:
            if fila["fecha"] == fecha:
                eliminado = True
                continue
            filas_nuevas.append(fila)

    if eliminado:
        with open(ARCHIVO, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["fecha", "entrada", "salida", "horas"])
            writer.writeheader()
            writer.writerows(filas_nuevas)
        print(f"Registro del día {fecha} eliminado correctamente.")
    else:
        print("No se encontró ningún registro con esa fecha.")

def menu():
    inicializar_csv()

    while True:
        print("\n--- Registro de horas de prácticas ---")
        print("1. Registrar entrada (automático)")
        print("2. Registrar salida (automático)")
        print("3. Registrar jornada manual")
        print("4. Ver total acumulado")
        print("5. Eliminar un día")
        print("6. Salir")

        opcion = input("Elige una opción: ")

        if opcion == "1":
            registrar_entrada()
        elif opcion == "2":
            registrar_salida()
        elif opcion == "3":
            registrar_manual()
        elif opcion == "4":
            mostrar_total()
        elif opcion == "5":
            eliminar_jornada()
        elif opcion == "6":
            break
        else:
            print("Opción no válida")

# ---------------- MAIN ---------------- #

def main():
    creds = autenticar()
    service = build('drive', 'v3', credentials=creds)

    descargar_csv(service)
    menu()
    subir_csv(service)

if __name__ == "__main__":
    main()
