#include <Arduino.h>
#include "BluetoothSerial.h"

const int LIGHT_READ_PIN = 36;
const int UP_BUTTON = 13;
const int DOWN_BUTTON = 4;
const int LEFT_BUTTON = 5;
const int RIGHT_BUTTON = 12;

//const int DARK_DIM_LIMIT = 1000;
//const int DIM_BRIGHT_LIMIT = 1500;


const int StateLED0 = 23;
const int StateLED1 = 22;
const int StateLED2 = 21;

const int Presses_Size = 20;
volatile char Presses[Presses_Size];
volatile int pressIndex = 0;

unsigned long previousMillis = 0;
const unsigned long interval = 500;

int State = 0;

BluetoothSerial SerialBT;

void IRAM_ATTR upButtonPress() {
  if (pressIndex < Presses_Size) { 
    Presses[pressIndex++] = 'U';
  }
}

void IRAM_ATTR downButtonPress() {
  if (pressIndex < Presses_Size) {
    Presses[pressIndex++] = 'D';
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
    
    int sum = 0;
    int max = -1;
    int min = 99999;
    for (int i=0; i < 18; i++){
      int analogValue = analogRead(LIGHT_READ_PIN);
      sum += analogValue; 
      if (analogValue > max){
        max = analogValue;
      }
      else if (analogValue < min){
        min = analogValue;
      }
      delay(10);
    }

    int averageRead = (sum - max - min)/16;

    String wiadomosc = 'S'+String(averageRead); //S2020
    SerialBT.println(wiadomosc);
  }


  if (pressIndex > 0) {
    for (int i = 0; i < pressIndex; i++) {
      SerialBT.println(Presses[i]); //U or D or L or R
    }
    pressIndex = 0; // Reset the index after reading presses
  }
  
  if (SerialBT.available()){
    char incoming = SerialBT.read();
    String wiadomosc = "State: " + String(incoming);

    if(incoming >= 48 && incoming <=55){
      State = incoming-48;
      delay(10);
    }
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

  delay(100);
}