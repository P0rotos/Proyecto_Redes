import requests
import time

API_URL = 'https://127.0.0.1:5000/api/readings'

# Hay que actualizar estos valores según el rango que esperamos de los sensores.
TEMP_MIN, TEMP_MAX = 50, 50
PRESSURE_MIN, PRESSURE_MAX = 950, 1050
HUMIDITY_MIN, HUMIDITY_MAX = 20, 80

def check_alerts(reading):
    alerts = []
    if not (TEMP_MIN <= reading['temperature'] <= TEMP_MAX):
        alerts.append(f"Temperatura fuera de rango: {reading['temperature']}")
    if not (PRESSURE_MIN <= reading['pressure'] <= PRESSURE_MAX):
        alerts.append(f"Presión fuera de rango: {reading['pressure']}")
    if not (HUMIDITY_MIN <= reading['humidity'] <= HUMIDITY_MAX):
        alerts.append(f"Humedad fuera de rango: {reading['humidity']}")
    return alerts

last_timestamp = None

# Cada 5 segundos, consulta la API para obtener las lecturas más recientes
while True:
    try:
        params = {}
        if last_timestamp:
            params['start_time'] = last_timestamp
        response = requests.get(API_URL, params=params, verify='cert.pem')
        data = response.json()
        # Ordenar de más antiguo a más nuevo
        data = sorted(data, key=lambda x: x['timestamp'])
        for reading in data:
            alerts = check_alerts(reading)
            for alert in alerts:
                print(f"ALERTA: {alert} (Sensor {reading['sensor_id']} en {reading['timestamp']})")
            last_timestamp = reading['timestamp']
    except Exception as e:
        print(f"Error consultando la API: {e}")
    time.sleep(5)