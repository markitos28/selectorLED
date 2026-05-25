#include <Servo.h>

#define NUM 5
int leds[NUM] = {3, 5, 6, 9, 10};   // Pines PWM para 5 LEDs
int brilloLeds[NUM];                
int ledSeleccionado = -1;

Servo servo1;
Servo servo2;

void setup() {
  Serial.begin(9600);

  // Inicializar LEDs
  for (int i = 0; i < NUM; i++) {
    pinMode(leds[i], OUTPUT);
    brilloLeds[i] = 0;
    analogWrite(leds[i], 0);
  }

  // Servos en pines 11 y 12 (no PWM, no afecta a los LEDs)
  servo1.attach(11);
  servo2.attach(12);
  servo1.write(0);
  servo2.write(0);
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    int p1 = input.indexOf(',');
    int p2 = input.indexOf(',', p1 + 1);
    if (p1 < 0 || p2 < 0) return;

    String modo = input.substring(0, p1);
    int v1 = input.substring(p1 + 1, p2).toInt();
    int v2 = input.substring(p2 + 1).toInt();

    if (modo == "LED") {
      if (v1 == 0) {
        for (int i = 0; i < NUM; i++) {
          brilloLeds[i] = 0;
          analogWrite(leds[i], 0);
        }
        ledSeleccionado = -1;
      } else if (v1 > 0 && v1 <= NUM) {
        int index = v1 - 1;
        ledSeleccionado = index;
        brilloLeds[index] = constrain(v2, 0, 255);
        analogWrite(leds[index], brilloLeds[index]);
      }

    } else if (modo == "SERVO") {
      if (v1 == 1) {
        if (v2 > 90) servo1.write(90);
        else servo1.write(0);
      } else if (v1 == 2) {
        if (v2 > 90) servo2.write(90);
        else servo2.write(0);
      }
    }
  }
}