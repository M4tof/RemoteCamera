#include <Arduino.h>
#include "BluetoothSerial.h"

const int LIGHT_READ_PIN = 36;
const int UP_BUTTON = 13;
const int DOWN_BUTTON = 4;
const int LEFT_BUTTON = 5;
const int RIGHT_BUTTON = 12;

const int StateLED0 = 23;
const int StateLED1 = 22;
const int StateLED2 = 21;

const int Presses_Size = 4;
volatile char Presses[Presses_Size];
volatile int pressIndex = 0;

unsigned long previousMillis = 0;
const unsigned long interval = 500;

int State = 0;

BluetoothSerial SerialBT;

const unsigned long debounceTime = 300;
unsigned long lastPressTime[4] = {0, 0, 0, 0};

// LED pattern variables
unsigned long patternMillis = 0;
const unsigned long patternInterval = 500; // 500ms per step
int patternStep = 0;

void IRAM_ATTR upButtonPress() {
  if (millis() - lastPressTime[0] >= debounceTime) {
    if (pressIndex < Presses_Size) {
      Presses[pressIndex++] = 'U';
      lastPressTime[0] = millis();
    }
  }
}

void IRAM_ATTR downButtonPress() {
  if (millis() - lastPressTime[1] >= debounceTime) {
    if (pressIndex < Presses_Size) {
      Presses[pressIndex++] = 'D';
      lastPressTime[1] = millis();
    }
  }
}

void IRAM_ATTR leftButtonPress() {
  if (millis() - lastPressTime[2] >= debounceTime) {
    if (pressIndex < Presses_Size) {
      Presses[pressIndex++] = 'L';
      lastPressTime[2] = millis();
    }
  }
}

void IRAM_ATTR rightButtonPress() {
  if (millis() - lastPressTime[3] >= debounceTime) {
    if (pressIndex < Presses_Size) {
      Presses[pressIndex++] = 'R';
      lastPressTime[3] = millis();
    }
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

void shiftLEDs() {
  switch (patternStep) {
    case 0: // LLH
      digitalWrite(StateLED0, LOW);
      digitalWrite(StateLED1, LOW);
      digitalWrite(StateLED2, HIGH);
      break;
    case 1: // LLL
      digitalWrite(StateLED0, LOW);
      digitalWrite(StateLED1, LOW);
      digitalWrite(StateLED2, LOW);
      break;
    case 2: // HLL
      digitalWrite(StateLED0, HIGH);
      digitalWrite(StateLED1, LOW);
      digitalWrite(StateLED2, LOW);
      break;
    case 3: // LHL
      digitalWrite(StateLED0, LOW);
      digitalWrite(StateLED1, HIGH);
      digitalWrite(StateLED2, LOW);
      break;
    case 4: // LLH
      digitalWrite(StateLED0, LOW);
      digitalWrite(StateLED1, LOW);
      digitalWrite(StateLED2, HIGH);
      break;
  }
  patternStep = (patternStep + 1) % 5; // Cycle through the pattern steps
}

void loop() {
  unsigned long currentMillis = millis();

  if (SerialBT.hasClient()) {
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
  }

  else{
    if (currentMillis - patternMillis >= patternInterval) {
      patternMillis = currentMillis;
      shiftLEDs();
    }
  }

  delay(50);
}
