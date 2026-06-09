void readBaro() {
    extern Adafruit_BMP085 bmp; 
    extern bool deviceExists(uint8_t addr);

    if (deviceExists(0x77)) {
        currentMeasurements.pressure = bmp.readPressure();
    } else {
        currentMeasurements.pressure = 0;
    }
}