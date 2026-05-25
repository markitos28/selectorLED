#include <Servo.h>

#define NUM_LEDS 3
int leds[NUM_LEDS] = {3, 5, 6};  // LEDs controlados por dedos 1–3

Servo servo1; // Servo del dedo 4 (pin 10)
Servo servo2; // Servo del dedo 5 (pin 11)

void setup() {
  Serial.begin(9600);

  // Inicializar LEDs
  for (int i = 0; i < NUM_LEDS; i++) {
    pinMode(leds[i], OUTPUT);
    analogWrite(leds[i], 0);
  }

  // Inicializar servos
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

      if (estadoDedos.length() == 5) {
        // ------------------------------
        // Control de LEDs (dedos 1 a 3)
        // ------------------------------
        for (int i = 0; i < 3; i++) {
          if (estadoDedos[i] == '1') {
            int valor = constrain(nivelBrillo, 0, 255);
            analogWrite(leds[i], valor);
          } else {
            analogWrite(leds[i], 0);
          }
        }

        // ------------------------------
        // Control independiente de servos
        // ------------------------------
        bool dedo4 = (estadoDedos[3] == '1');
        bool dedo5 = (estadoDedos[4] == '1');

        if (dedo4 && !dedo5) {
          // Solo dedo 4 levantado
          servo1.write(180);
          servo2.write(0);
        } 
        else if (dedo5 && !dedo4) {
          // Solo dedo 5 levantado
          servo2.write(180);
          servo1.write(0);
        } 
        else {
          // Ambos o ninguno levantados
          servo1.write(0);
          servo2.write(0);
        }
      }
    }
  }
}
