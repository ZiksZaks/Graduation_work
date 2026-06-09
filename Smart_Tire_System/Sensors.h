#ifndef SENSORS_H
#define SENSORS_H

struct AllData {
  int16_t ax, ay, az; 
  float lux;          
  long pressure;      
};

extern AllData currentMeasurements;

#endif