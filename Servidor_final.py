# app.py (Servidor Final)
from flask import Flask, request, jsonify, render_template, abort
import sqlite3
from datetime import datetime
import json
from werkzeug.exceptions import RequestEntityTooLarge
from OpenSSL import SSL

app = Flask(__name__)
DATABASE = 'sensor_data.db'

# Limit request size to 1MB
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            temperature REAL NOT NULL,
            pressure REAL NOT NULL,
            humidity REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.after_request
def set_secure_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.errorhandler(RequestEntityTooLarge)
def handle_large_request(e):
    return jsonify({"status": "error", "message": "Request too large"}), 413

def validate_sensor_data(data):
    required = {
        'sensor_id': int,
        'timestamp': str,
        'temperature': (float, int),
        'pressure': (float, int),
        'humidity': (float, int)
    }
    for key, typ in required.items():
        if key not in data:
            return False, f"Missing field: {key}"
        if not isinstance(data[key], typ):
            # Allow string timestamp (ISO format)
            if key == 'timestamp' and isinstance(data[key], str):
                continue
            return False, f"Invalid type for {key}"
    return True, ""

@app.route('/data', methods=['POST'])
def receive_data():
    try:
        if not request.is_json:
            return jsonify({"status": "error", "message": "Invalid content type"}), 400
        data = request.get_json()
        valid, msg = validate_sensor_data(data)
        if not valid:
            return jsonify({"status": "error", "message": msg}), 400

        sensor_id = data['sensor_id']
        timestamp = data['timestamp']
        temperature = float(data['temperature'])
        pressure = float(data['pressure'])
        humidity = float(data['humidity'])

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sensor_readings (sensor_id, timestamp, temperature, pressure, humidity) VALUES (?, ?, ?, ?, ?)",
            (sensor_id, timestamp, temperature, pressure, humidity)
        )
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Data received and stored"}), 200
    except Exception as e:
        # Log the error internally, but don't expose details to the client
        import logging
        logging.exception("Error processing /data request")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/api/readings', methods=['GET'])
def get_readings():
    sensor_id = request.args.get('sensor_id')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    query = "SELECT sensor_id, timestamp, temperature, pressure, humidity FROM sensor_readings WHERE 1=1"
    params = []

    if sensor_id:
        query += " AND sensor_id = ?"
        params.append(sensor_id)
    if start_time:
        query += " AND timestamp >= ?"
        params.append(start_time)
    if end_time:
        query += " AND timestamp <= ?"
        params.append(end_time)

    #Ordenar Para nuevos primero
    query += " ORDER BY timestamp DESC" 

    cursor.execute(query, params)
    readings = cursor.fetchall()
    conn.close()

    results = []
    for row in readings:
        results.append({
            "sensor_id": row[0],
            "timestamp": row[1],
            "temperature": row[2],
            "pressure": row[3],
            "humidity": row[4]
        })
    return jsonify(results)

if __name__ == '__main__':
    init_db()
    app.run(
        debug=False,
        host='0.0.0.0',
        port=5000,
        ssl_context=('cert.pem', 'key.pem')
    )