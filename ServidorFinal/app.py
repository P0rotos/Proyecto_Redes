# app.py (Servidor Final)
from flask import Flask, request, jsonify, render_template
import sqlite3
from datetime import datetime
import json

app = Flask(__name__)
DATABASE = 'sensor_data.db'

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

@app.route('/data', methods=['POST'])
def receive_data():
    try:
        data = request.json
        sensor_id = data['sensor_id']
        timestamp = data['timestamp'] 
        temperature = data['temperature']
        pressure = data['pressure']
        humidity = data['humidity']

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
        return jsonify({"status": "error", "message": str(e)}), 400

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
    app.run(debug=True, host='0.0.0.0', port=5000)