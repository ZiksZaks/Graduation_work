import sqlite3
import paho.mqtt.client as mqtt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json
import os

app = FastAPI()
app.add_middleware(
CORSMiddleware, 
allow_origins=["*"], 
allow_credentials=True, 
allow_methods=["*"], 
allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sensors.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payload TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("БАЗА ДАННЫХ: Инициализирована")

def save_to_db(payload_str):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO readings (payload) VALUES (?)
        ''', (payload_str,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"ОШИБКА ЗАПИСИ В БД: {e}")


def on_connect(client, userdata, flags, rc):
    print(f"MQTT: Подключено с кодом {rc}")
    client.subscribe("esp32/sensors")

def on_message(client, userdata, message):
    try:
        payload = message.payload.decode("utf-8").strip()
        
        try:
            data = json.loads(payload)
            save_to_db(payload)
            print(f"MQTT: Получен готовый JSON-пакет: {data}")
            return
        except json.JSONDecodeError:
            pass

        parts = payload.split(',')
        if len(parts) == 5:
            data = {
                "ax": float(parts[0]),
                "ay": float(parts[1]),
                "az": float(parts[2]),
                "lux": float(parts[3]),
                "pressure": float(parts[4])
            }
            json_payload = json.dumps(data)
            save_to_db(json_payload)
            print(f"MQTT: Успешно обработана старая строка и сохранена как JSON: {data}")
        else:
            print(f"MQTT: Ошибка! Неверный формат строки : {payload}")
            
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
    return {"status": "online", "message": "Smart Stand API (Hybrid Mode) is running"}

@app.get("/history")
async def get_history():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT payload, timestamp 
            FROM readings 
            ORDER BY id DESC 
            LIMIT 20
        ''')
        rows = cursor.fetchall()
        conn.close()

        result = []
        for r in rows:
            sensor_data = json.loads(r[0])
            sensor_data["timestamp"] = r[1]
            result.append(sensor_data)
        
        return result[::-1]
    
    except Exception as e:
        return {"error": str(e)}
