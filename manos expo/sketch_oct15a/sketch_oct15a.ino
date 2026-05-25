#include <Servo.h>

#define NUM_LEDS 3
int leds[NUM_LEDS] = {3, 5, 6};  // LEDs en dedos 1–3
int brilloLeds[NUM_LEDS];

Servo servo1; // dedo 4
Servo servo2; // dedo 5

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < NUM_LEDS; i++) {
    pinMode(leds[i], OUTPUT);
    analogWrite(leds[i], 0);
    brilloLeds[i] = 0;
  }

  servo1.attach(10);
  servo2.attach(11);
  servo1.write(0);
  servo2.write(0);
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    int coma = input.indexOf(',');

    if (coma > 0) {
      String estadoDedos = input.substring(0, coma);
      int nivelBrillo = input.substring(coma + 1).toInt();

      // Asegurar que tenga 5 caracteres
      if (estadoDedos.length() == 5) {
        // LEDS (dedos 1, 2, 3)
        for (int i = 0; i < 3; i++) {
          if (estadoDedos[i] == '1') {
            int valor = constrain(nivelBrillo, 0, 255);
            if (valor > 0 && valor < 15) valor = 15;
            analogWrite(leds[i], valor);
            brilloLeds[i] = valor;
          } else {
            analogWrite(leds[i], 0);
            brilloLeds[i] = 0;
          }
        }

        // SERVO 1 (dedo 4)
        if (estadoDedos[3] == '1') {
          servo1.write(180);
        } else {
          servo1.write(0);
        }

        // SERVO 2 (dedo 5)
        if (estadoDedos[4] == '1') {
          servo2.write(180);
        } else {
          servo2.write(0);
        }
      }
    }
  }
}