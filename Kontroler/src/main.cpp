#include <Arduino.h>

const int LIGHT_READ_PIN = 36;
const int DARK_DIM_LIMIT = 1000;
const int DIM_BRIGHT_LIMIT = 1500;

void setup() {
  Serial.begin(9600);

  analogSetAttenuation(ADC_11db);
}

void loop() {
  int analogValue = analogRead(LIGHT_READ_PIN);
  Serial.print("Analog Value = ");
  Serial.print(analogValue);

  if(analogValue <= DARK_DIM_LIMIT){
    Serial.println(" Is Dark");
  }
  else if (analogValue <= DIM_BRIGHT_LIMIT)
  {
    Serial.println(" Is Dim");
  }
  else{
    Serial.println(" Is Bright");
  }
  

  delay(200);
}