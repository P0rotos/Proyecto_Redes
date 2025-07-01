import requests
import json
from datetime import datetime
import random

url = "http://127.0.0.1:5000/data"
headers = {'Content-Type': 'application/json'}

for i in range(5):
    sensor_data = {
        "sensor_id": 101,
        "timestamp": datetime.now().isoformat(),
        "temperature": round(random.uniform(20.0, 30.0), 2),
        "pressure": round(random.uniform(1000.0, 1020.0), 2),
        "humidity": round(random.uniform(40.0, 60.0), 2)
    }
    response = requests.post(url, headers=headers, data=json.dumps(sensor_data))
    print(f"Sent data: {sensor_data} -> Response: {response.json()}")