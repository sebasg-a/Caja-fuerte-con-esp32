import serial
import base64
import os
from datetime import datetime

PUERTO = "COM7"  # Cambia esto por tu COM real
BAUDRATE = 115200

PERSONA = "sebas"
DATASET_DIR = "dataset"

MARCA_INICIO = "###IMG_START###"
MARCA_FIN = "###IMG_END###"


def crear_carpeta_dataset():
    carpeta = os.path.join(DATASET_DIR, PERSONA)
    os.makedirs(carpeta, exist_ok=True)
    return carpeta


def recibir_fotos():
    carpeta = crear_carpeta_dataset()

    print("Abriendo puerto:", PUERTO)

    with serial.Serial(PUERTO, BAUDRATE, timeout=5) as ser:
        print("Escuchando fotos desde ESP32...")
        print("Guardando en:", carpeta)

        while True:
            linea = ser.readline().decode(errors="ignore").strip()

            if not linea:
                continue

            print("ESP32:", linea)

            if linea == MARCA_INICIO:
                nombre_archivo = ser.readline().decode(errors="ignore").strip()
                size_line = ser.readline().decode(errors="ignore").strip()

                try:
                    size_esperado = int(size_line)
                except ValueError:
                    print("Tamano invalido:", size_line)
                    continue

                print("Recibiendo:", nombre_archivo)
                print("Tamano esperado:", size_esperado)

                base64_lines = []

                while True:
                    data_line = ser.readline().decode(errors="ignore").strip()

                    if data_line == MARCA_FIN:
                        break

                    if data_line:
                        base64_lines.append(data_line)

                try:
                    imagen_base64 = "".join(base64_lines)
                    imagen_bytes = base64.b64decode(imagen_base64)

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    nombre_final = f"{timestamp}_{nombre_archivo}"
                    ruta = os.path.join(carpeta, nombre_final)

                    with open(ruta, "wb") as f:
                        f.write(imagen_bytes)

                    print("Guardada:", ruta)
                    print("Bytes recibidos:", len(imagen_bytes))

                    if len(imagen_bytes) != size_esperado:
                        print("ADVERTENCIA: tamano diferente al esperado")

                except Exception as e:
                    print("Error guardando imagen:", e)


if __name__ == "__main__":
    recibir_fotos()