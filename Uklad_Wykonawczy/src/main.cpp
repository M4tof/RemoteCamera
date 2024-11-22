#include <Arduino.h>
#include <Servo.h>

const int LED = 3;
const int BASE_SERVO = 5;
const int UPPER_SERVO = 6;

Servo base_servo;
Servo upper_servo;

void setup() {
  Serial.begin(9600);
  base_servo.attach(BASE_SERVO);
  upper_servo.attach(UPPER_SERVO);

  pinMode(LED, OUTPUT);
  base_servo.write(90); // Ustawienie domyślnej pozycji
  upper_servo.write(90); // Ustawienie domyślnej pozycji

  // delay(50000);
}

void loop() {
  if (Serial.available() > 0) {
    char input = Serial.read(); // Odczytaj pierwszy znak
    int value = Serial.parseInt(); // Odczytaj liczbę całkowitą

    Serial.print("Command: ");
    Serial.println(input);
    Serial.print("Value: ");
    Serial.println(value);

    switch (input) {
      case 'b': // Ustawienie pozycji base_servo
        if (value >= 0 && value <= 180) {
          base_servo.write(value);
        } else {
          Serial.println("Base servo value out of range (0-180).");
        }
        break;

      case 'u': // Ustawienie pozycji upper_servo
        if (value >= 20 && value <= 160) {
          upper_servo.write(value);
        } else {
          Serial.println("Upper servo value out of range (20-160).");
        }
        break;

      case 'l': // Ustawienie jasności LED
        if (value >= 0 && value <= 255) {
          analogWrite(LED, value);
        } else {
          Serial.println("LED brightness value out of range (0-255).");
        }
        break;

      default:
        Serial.println("Invalid command. Use 'b', 'u', or 'l'.");
        break;
    }
  }
  delay(5000);
}
