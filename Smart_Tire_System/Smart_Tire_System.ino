#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_BMP085.h>
#include <BH1750.h>
#include "Sensors.h"


const char* ssid = "Имя_Сети";
const char* password = "Пароль_Сети";


Adafruit_BMP085 bmp;
BH1750 lightMeter;
AllData currentMeasurements; 
WiFiClient espClient;
PubSubClient client(espClient);


const char* mqtt_server = "192.168.0.18"; 


void readMPU();
void readLight();
void readBaro();

bool deviceExists(uint8_t addr) {
    Wire.beginTransmission(addr);
    return (Wire.endTransmission() == 0);
}

void reconnect() {
    while (!client.connected()) {
        Serial.print("Попытка подключения к MQTT (" + String(mqtt_server) + ")...");
        if (client.connect("ESP32_Smart_Bus")) {
            Serial.println("Успешно!");
        } else {
            Serial.print("Ошибка rc=");
            Serial.print(client.state());
            Serial.println(" пробуем через 5 сек");
            delay(5000);
        }
    }
}


void printReport() {
    Serial.println("\n>>> ТЕКУЩИЕ ПОКАЗАТЕЛИ:");
    Serial.printf("[MPU6050] X: %d | Y: %d | Z: %d\n", currentMeasurements.ax, currentMeasurements.ay, currentMeasurements.az);
    Serial.printf("[BH1750]  Свет: %.2f lx\n", currentMeasurements.lux);
    Serial.printf("[BMP180]  Давление: %ld Pa\n", currentMeasurements.pressure); 
    Serial.println("--------------------------------");
}

void setup() {
    Serial.begin(115200);
    
    Serial.println();
    Serial.print("Подключение к сети: ");
    Serial.println(ssid);

    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println("");
    Serial.println("WiFi подключен успешно!");
    Serial.print("IP адрес ESP32: ");
    Serial.println(WiFi.localIP());

    client.setServer(mqtt_server, 1883);
    
    Wire.begin(21, 22);
    Wire.setClock(100000);

    // Запускаем датчики, если они откликаются по I2C
    if (deviceExists(0x77)) bmp.begin();
    if (deviceExists(0x23)) lightMeter.begin();

    Serial.println("Система мониторинга инициализирована.");
}

void loop() {
    if (!client.connected()) {
        reconnect();
    }
    client.loop();


    readMPU();   
    readLight(); 
    readBaro();  
    
    printReport(); 

    String payload = String(currentMeasurements.ax) + "," + 
                     String(currentMeasurements.ay) + "," + 
                     String(currentMeasurements.az) + "," + 
                     String(currentMeasurements.lux) + "," + 
                     String(currentMeasurements.pressure);

    if (client.publish("esp32/sensors", payload.c_str())) {
        Serial.println("Данные отправлены в MQTT");
    }

    delay(3000);
}
