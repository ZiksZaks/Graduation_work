void readLight() {
    extern BH1750 lightMeter;
    extern bool deviceExists(uint8_t addr);

    if (deviceExists(0x23)) {
        currentMeasurements.lux = lightMeter.readLightLevel();
    } else {
        currentMeasurements.lux = 0;
    }
}