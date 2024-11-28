#include <Arduino.h>
#include <Servo.h>

const int LED = 3;
const int BASE_SERVO = 5;
const int UPPER_SERVO = 6;

unsigned long previousMillis = 0;
const unsigned long interval = 500;

Servo base_servo;
Servo upper_servo;

String inputString = "";  // Stores the received string
boolean stringComplete = false;

void setup() {
  Serial.begin(9600);
  base_servo.attach(BASE_SERVO);
  upper_servo.attach(UPPER_SERVO);

  pinMode(LED, OUTPUT);
  base_servo.write(90); // Setting default position
  upper_servo.write(90);

  // delay(5000); //For assembling the device for the first time with resetting servo position
}

void loop() {
  if (stringComplete) {
    char command = inputString[0];  // First character
    int value = inputString.substring(1).toInt();  // Rest of the string as an integer

    switch (command) {
      case 'b':
        if (value >= 0 && value <= 180) base_servo.write(value);
        break;
      case 'u':
        if (value >= 20 && value <= 160) upper_servo.write(value);
        break;
      case 'l':
        if (value >= 0 && value <= 255) analogWrite(LED, value);
        break;
      default:
        Serial.println("E");  // Error message for invalid command
        break;
    }

    inputString = "";  // Clear the string for the next command
    stringComplete = false;
  }

  // Heartbeat signal
  if (millis() - previousMillis >= interval) {
    previousMillis = millis();
    Serial.println("A");
  }
}

void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') {  // End of a command
      stringComplete = true;
    } else {
      inputString += inChar;  // Append character to input string
    }
  }
}
