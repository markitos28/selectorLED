#include <Servo.h>

#define NUM_LEDS 3
int leds[NUM_LEDS] = {3, 5, 6}; // Pines PWM para LEDs
int brilloLeds[NUM_LEDS];
int ledSeleccionado = -1;

Servo servo1;
Servo servo2;

void setup() {
  Serial.begin(9600);

  // Inicializar LEDs apagados
  for (int i = 0; i < NUM_LEDS; i++) {
    pinMode(leds[i], OUTPUT);
    brilloLeds[i] = 0;
    analogWrite(leds[i], 0);
  }

  // Servos
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
      int dedo = input.substring(0, coma).toInt();
      int nivelBrillo = input.substring(coma + 1).toInt();

      // Reinicio total
      if (dedo == 0) {
        for (int i = 0; i < NUM_LEDS; i++) {
          analogWrite(leds[i], 0);
          brilloLeds[i] = 0;
        }
        servo1.write(0);
        servo2.write(0);
        ledSeleccionado = -1;
        return;
      }

      // DEDOS 1–3 → LEDs
      if (dedo >= 1 && dedo <= 3) {
        int index = dedo - 1;
        int valor = constrain(nivelBrillo, 0, 255);
        if (valor > 0 && valor < 15) valor = 15;

        brilloLeds[index] = valor;
        analogWrite(leds[index], valor);
        ledSeleccionado = index;
      }

      // DEDO 4 → Servo 1 (sin brillo)
      if (dedo == 4) {
        servo1.write(180);   // posición activa
             // volver a 0
      }

      // DEDO 5 → Servo 2 (sin brillo)
      if (dedo == 5) {
        servo2.write(180);
      }
    }
  }
}