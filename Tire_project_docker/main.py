import sqlite3
import paho.mqtt.client as mqtt
from fastapi import FastAPI
from typing import List
import json

app = FastAPI()
DB_PATH = "sensors.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ax REAL, ay REAL, az REAL,
            lux REAL,
            pressure REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("БАЗА ДАННЫХ: Инициализирована")

def save_to_db(data):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO readings (ax, ay, az, lux, pressure)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['ax'], data['ay'], data['az'], data['lux'], data['pressure']))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"ОШИБКА ЗАПИСИ В БД: {e}")


def on_connect(client, userdata, flags, rc):
    print(f"MQTT: Подключено с кодом {rc}")
    client.subscribe("esp32/sensors")

def on_message(client, userdata, message):
    try:
        payload = message.payload.decode("utf-8")
        parts = payload.split(',')
        
        if len(parts) == 5:
            data = {
                "ax": float(parts[0]),
                "ay": float(parts[1]),
                "az": float(parts[2]),
                "lux": float(parts[3]),
                "pressure": float(parts[4])
            }
            save_to_db(data)
            print(f"MQTT: Получены данные: {data}")
        else:
            print(f"MQTT: Неверный формат данных (нужно 5 значений, пришло {len(parts)})")
            
    except Exception as e:
        print(f"MQTT: Ошибка обработки сообщения: {e}")


mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message


try:
    mqtt_client.connect("mqtt_service", 1883, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"MQTT: Не удалось запустить клиент: {e}")


init_db()



@app.get("/")
async def root():
    return {"status": "online", "message": "Smart Stand API is running"}

@app.get("/history")
async def get_history():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Берем последние 20 записей, сортируем по ID
        cursor.execute('''
            SELECT ax, ay, az, lux, pressure 
            FROM readings 
            ORDER BY id DESC 
            LIMIT 20
        ''')
        rows = cursor.fetchall()
        conn.close()

        result = []
        for r in rows:
            result.append({
                "ax": r[0],
                "ay": r[1],
                "az": r[2],
                "lux": r[3],
                "pressure": r[4]
            })
        
        return result[::-1]
    
    except Exception as e:
        return {"error": str(e)}