from pymodbus.client import ModbusTcpClient
import time


def leer_registros_modbus():
    # Crear cliente Modbus TCP
    cliente = ModbusTcpClient(host='localhost', port=5020)

    try:
        # Intentar conectar
        if not cliente.connect():
            print("No se pudo conectar al servidor Modbus")
            return

        print("Conectado al servidor Modbus")

        # Leer los registros holding (donde se almacenan los datos)
        resultado = cliente.read_holding_registers(address=0, count=9, slave=1)

        if resultado is None or resultado.isError():
            print("Error al leer los registros")
            return

        # Interpretar los valores
        id_sensor = resultado.registers[0]
        temp_high = resultado.registers[1]
        temp_low = resultado.registers[2]
        temperatura = ((temp_high << 16) | temp_low) / 100.0

        pres_high = resultado.registers[3]
        pres_low = resultado.registers[4]
        presion = ((pres_high << 16) | pres_low) / 100.0

        hum_high = resultado.registers[5]
        hum_low = resultado.registers[6]
        humedad = ((hum_high << 16) | hum_low) / 100.0

        timestamp_high = resultado.registers[7]
        timestamp_low = resultado.registers[8]
        timestamp = (timestamp_high << 16) | timestamp_low

        print("\nValores actuales:")
        print(f"Registros crudos: {resultado.registers}")
        print(f"ID Sensor: {id_sensor}")
        print(f"Temperatura: {temperatura}°C")
        print(f"Presión: {presion} hPa")
        print(f"Humedad: {humedad}%")
        print(f"Timestamp: {timestamp}")

    except Exception as e:
        print(f"Error: {str(e)}")

    finally:
        cliente.close()
        print("Conexión cerrada")


# Bucle principal para leer continuamente
if __name__ == "__main__":
    print("Presiona Ctrl+C para detener")
    try:
        while True:
            leer_registros_modbus()
            time.sleep(2)  # Esperar 2 segundos entre lecturas
    except KeyboardInterrupt:
        print("\nLectura detenida por el usuario")