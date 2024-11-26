#include <Arduino.h>
#include <Servo.h>

const int LED = 3;
const int BASE_SERVO = 5;
const int UPPER_SERVO = 6;

unsigned long previousMillis = 0;
const unsigned long interval = 500;

Servo base_servo;
Servo upper_servo;

void setup() {
  Serial.begin(9600);
  base_servo.attach(BASE_SERVO);
  upper_servo.attach(UPPER_SERVO);

  pinMode(LED, OUTPUT);
  base_servo.write(90); // Setting default position
  upper_servo.write(90);

  // delay(50000); //For assembling the device for the first time with resetting servo position
}

void loop() {
  if (Serial.available() > 0) {
    char input = Serial.read(); // Read first char
    int value = Serial.parseInt(); // Read integer

    // Serial.print("Command: ");
    // Serial.println(input);     //For debug purposes
    // Serial.print("Value: ");
    // Serial.println(value);

    switch (input) {
      case 'b': // Base servo
        if (value >= 0 && value <= 180) {
          base_servo.write(value);
        }
        break;

      case 'u': //upper_servo
        if (value >= 20 && value <= 160) {
          upper_servo.write(value);
        }
        break;

      case 'l': // LED brightness
        if (value >= 0 && value <= 255) {
          analogWrite(LED, value);
        }
        break;

      default:
        Serial.println("Incorrect Info");
        break;
    }
  }

  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    Serial.println("Arduino Alive"); //Heartbeat of the arduino to signalise the central_unit that the executive_components are working
  }

  delay(200);
}
