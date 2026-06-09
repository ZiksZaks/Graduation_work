void readMPU() {
    extern bool deviceExists(uint8_t addr);
    
    if (deviceExists(0x68)) {

    } else {
        currentMeasurements.ax = 0;
        currentMeasurements.ay = 0;
        currentMeasurements.az = 0;
    }
}