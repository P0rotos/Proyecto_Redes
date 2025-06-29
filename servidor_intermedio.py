from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key
import socket
import struct
import threading
import requests
import json
from datetime import datetime
import logging

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO
)
logger = logging.getLogger()

# !! pip install pymodbus y pip install cryptography !!

# como el trabajo pide usar modbus, y también transformar datos a formato texto reenviados al server final,
# hice ambos :p

# Empecé con el supuesto de que usamos RSA 2048, las claves fueron generadas con openssl

# CONFIGURACIÓN: todo: hay q modificar estos valores para q cuadre con el sensor y server final
BYTES_DE_DATOS = 22  # 2 + 8 + 4 + 4 + 4
PUERTO_RECEPCION = 12345
IP_RECEPCION = "127.0.0.1"
PUERTO_MODBUS = 5020
SERVIDOR_FINAL_URL = "http://localhost:8000/datos"

# Inicializar almacenamiento Modbus (tienen parte alta y baja porque los registros almacenan 16 bits)
# Registros:
# 0: ID Sensor
# 1: Temperatura (parte alta)
# 2: Temperatura (parte baja)
# 3: Presión (parte alta)
# 4: Presión (parte baja)
# 5: Humedad (parte alta)
# 6: Humedad (parte baja)
# 7: Timestamp (parte alta)
# 8: Timestamp (parte baja)
store = ModbusSlaveContext(
    hr=ModbusSequentialDataBlock(0, [0] * 9),
)
context = ModbusServerContext(slaves=store, single=True)

def actualizar_registros_modbus(datos):
    try:
        # Separar valores en dos partes de 16 bits
        # Temperatura (primero multiplicarla por 100)
        temp_high = (int(datos['temperatura'] * 100) >> 16) & 0xFFFF
        temp_low = (int(datos['temperatura'] * 100)) & 0xFFFF

        # Presión (primer multiplicarla por 100)
        pres_high = (int(datos['presion'] * 100) >> 16) & 0xFFFF
        pres_low = (int(datos['presion'] * 100)) & 0xFFFF

        # Humedad (primero multiplicarla por 100)
        hum_high = (int(datos['humedad'] * 100) >> 16) & 0xFFFF
        hum_low = (int(datos['humedad'] * 100)) & 0xFFFF

        # Timestamp
        ts_high = (datos['timestamp'] >> 16) & 0xFFFF
        ts_low = datos['timestamp'] & 0xFFFF

        valores = [
            datos['ID'],
            temp_high, temp_low,
            pres_high, pres_low,
            hum_high, hum_low,
            ts_high, ts_low
        ]

        logger.info(f"Actualizando registros Modbus con valores: {valores}")
        store.setValues(3, 0, valores)

        # Verificar los valores almacenados
        hr_values = store.getValues(3, 0, 9)
        logger.info(f"Valores actuales en registros holding: {hr_values}")

    except Exception as e:
        logger.error(f"Error al actualizar registros Modbus: {e}", exc_info=True)


# Cargar clave pública
try:
    with open("public.pem", "rb") as f:
        clave_publica = load_pem_public_key(f.read())
    print("Clave pública cargada correctamente")
except Exception as e:
    logger.error(f"Error al cargar la clave pública: {e}", exc_info=True)
    exit(1)


def enviar_al_servidor_final(datos):

    try:
        response = requests.post(
            SERVIDOR_FINAL_URL,
            json=datos,
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 200:
            logger.info(f"Datos enviados correctamente al servidor final")
        else:
            logger.error(f"Error al enviar datos: {response.status_code}", exc_info=True)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en la conexión con el servidor final: {e}")


# servidor que recibe datos binarios, verifica firma y procesa datos
def servidor_tcp():

    s = socket.socket()
    s.bind((IP_RECEPCION, PUERTO_RECEPCION))
    s.listen()
    print(f"Servidor intermedio escuchando en {IP_RECEPCION}:{PUERTO_RECEPCION}")

    while True:
        conn, addr = s.accept()
        logger.info(f"Conexión recibida desde {addr}")
        data = conn.recv(1024)

        if len(data) >= BYTES_DE_DATOS:
            paquete = data[:BYTES_DE_DATOS] # Sección de paquete que contiene los datos
            firma = data[BYTES_DE_DATOS:] # Sección del paquete que tiene firma rsa

            try:
                # Verificar firma
                clave_publica.verify(
                    firma,
                    paquete,
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )

                # desempaqueta datos
                id_sensor, timestamp, temperatura, presion, humedad = struct.unpack(
                    "<hqfff",
                    paquete
                )

                # crea diccionario con los datos
                datos_json = {
                    "ID": id_sensor,
                    "timestamp": timestamp,
                    "fecha_hora": datetime.fromtimestamp(timestamp).isoformat(),
                    "temperatura": round(temperatura, 2),
                    "presion": round(presion, 2),
                    "humedad": round(humedad, 2)
                }

                print(f"[VALIDADO] Datos recibidos: {json.dumps(datos_json, indent=2)}")

                # actualiza registros Modbus
                actualizar_registros_modbus(datos_json)

                # envia al servidor final
                enviar_al_servidor_final(datos_json)

            except Exception as e:
                logger.error(f"Error en la verificación o procesamiento: {e}")
        else:
            logger.error(f"Datos recibidos insuficientes: {len(data)} bytes")

        conn.close()


def iniciar_servidor():
    # Iniciar servidor TCP en un hilo separado
    thread_tcp = threading.Thread(target=servidor_tcp, daemon=True)
    thread_tcp.start()

    print(f"Iniciando servidor Modbus TCP en puerto {PUERTO_MODBUS}")
    # Iniciar servidor Modbus
    try:
        StartTcpServer(
            context,
            address=("localhost", PUERTO_MODBUS)
        )
    except Exception as e:
        logger.error(f"Error al iniciar servidor Modbus: {e}", exc_info=True)

if __name__ == "__main__":
    iniciar_servidor()
