#include <Arduino.h>
#include "BluetoothSerial.h"

const int LIGHT_READ_PIN = 36;
const int UP_BUTTON = 13;
const int DOWN_BUTTON = 4;
const int LEFT_BUTTON = 5;
const int RIGHT_BUTTON = 12;

const int DARK_DIM_LIMIT = 1000;
const int DIM_BRIGHT_LIMIT = 1500;

const int StateLED0 = 23;
const int StateLED1 = 22;
const int StateLED2 = 21;

const int Presses_Size = 20;
volatile char Presses[Presses_Size];
volatile int pressIndex = 0;

unsigned long previousMillis = 0;
const unsigned long interval = 5000;

volatile int State = 0;

BluetoothSerial SerialBT;

void IRAM_ATTR upButtonPress() {
  if (pressIndex < Presses_Size) { 
    Presses[pressIndex++] = 'U';
    State++;
    if(State >= 8){
      State = 0;
    }
  }
}

void IRAM_ATTR downButtonPress() {
  if (pressIndex < Presses_Size) {
    Presses[pressIndex++] = 'D';
    State--;
    if (State <= -1){
      State = 7;
    }
  }
}

void IRAM_ATTR leftButtonPress() {
  if (pressIndex < Presses_Size) {
    Presses[pressIndex++] = 'L';
  }
}

void IRAM_ATTR rightButtonPress() {
  if (pressIndex < Presses_Size) {
    Presses[pressIndex++] = 'R';
  }
}

void setup() {
  Serial.begin(9600);
  SerialBT.begin("Wireless Controller ESP32");

  analogSetAttenuation(ADC_11db);

  pinMode(UP_BUTTON,INPUT_PULLUP);
  pinMode(DOWN_BUTTON,INPUT_PULLUP);
  pinMode(LEFT_BUTTON,INPUT_PULLUP);
  pinMode(RIGHT_BUTTON,INPUT_PULLUP);
  pinMode(StateLED0,OUTPUT);
  pinMode(StateLED1,OUTPUT);
  pinMode(StateLED2,OUTPUT);

  attachInterrupt(digitalPinToInterrupt(UP_BUTTON), upButtonPress, FALLING);
  attachInterrupt(digitalPinToInterrupt(DOWN_BUTTON), downButtonPress, FALLING);
  attachInterrupt(digitalPinToInterrupt(LEFT_BUTTON), leftButtonPress, FALLING);
  attachInterrupt(digitalPinToInterrupt(RIGHT_BUTTON), rightButtonPress, FALLING);

  digitalWrite(StateLED0,LOW);
  digitalWrite(StateLED1,LOW);
  digitalWrite(StateLED2,LOW);
}

void loop() {
  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    
    int analogValue = analogRead(LIGHT_READ_PIN);
    Serial.print("Analog Value = ");
    Serial.print(analogValue);
    String wiadomosc = 'S' + String(analogValue);
    SerialBT.println(wiadomosc);

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
  }


  if (pressIndex > 0) {
    Serial.print("Button Presses: ");
    for (int i = 0; i < pressIndex; i++) {
      Serial.print(Presses[i]);
      Serial.print(" ");
      SerialBT.print(Presses[i]);
    }
    Serial.println();
    SerialBT.println();
    pressIndex = 0; // Reset the index after reading presses
  }

  switch (State) {
  case 0:
    digitalWrite(StateLED0,LOW);
    digitalWrite(StateLED1,LOW);
    digitalWrite(StateLED2,LOW);
    break;
  case 1:
    digitalWrite(StateLED0,HIGH);
    digitalWrite(StateLED1,LOW);
    digitalWrite(StateLED2,LOW);
    break;
  case 2:
    digitalWrite(StateLED0,LOW);
    digitalWrite(StateLED1,HIGH);
    digitalWrite(StateLED2,LOW);
    break;
  case 3:
    digitalWrite(StateLED0,HIGH);
    digitalWrite(StateLED1,HIGH);
    digitalWrite(StateLED2,LOW);
    break;
  case 4:
    digitalWrite(StateLED0,LOW);
    digitalWrite(StateLED1,LOW);
    digitalWrite(StateLED2,HIGH);
    break;
  case 5:
    digitalWrite(StateLED0,HIGH);
    digitalWrite(StateLED1,LOW);
    digitalWrite(StateLED2,HIGH);
    break;
  case 6:
    digitalWrite(StateLED0,LOW);
    digitalWrite(StateLED1,HIGH);
    digitalWrite(StateLED2,HIGH);
    break;
  default:
    digitalWrite(StateLED0,HIGH);
    digitalWrite(StateLED1,HIGH);
    digitalWrite(StateLED2,HIGH);
    break;
}
  delay(200);
}