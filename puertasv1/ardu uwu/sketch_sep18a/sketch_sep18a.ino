#include <Servo.h>


#define NUM 5
int leds[NUM] = {3, 5, 6, 9, 10}; // Pines PWM para LEDs

int brilloLeds[NUM];   // guarda el brillo actual de cada LED
int ledSeleccionado = -1; // LED actualmente seleccionado para modificar brillo

// --- Servos ---
Servo servo1;
Servo servo2;
int pinServo1 = 2;  // Cambiá si usás otros pines
int pinServo2 = 12;

void setup() {
  Serial.begin(9600);

  // Inicializar LEDs apagados
  for (int i = 0; i < NUM; i++) {
    pinMode(leds[i], OUTPUT);
    brilloLeds[i] = 0;
    analogWrite(leds[i], 0);
  }

  // Inicializar servos
  servo1.attach(pinServo1);
  servo2.attach(pinServo2);
  servo1.write(90); // posición de reposo
  servo2.write(90);
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    int coma = input.indexOf(',');

    if (coma > 0) {
      int ledSelect = input.substring(0, coma).toInt();
      int nivelBrillo = input.substring(coma + 1).toInt();

      // --- Control de servos ---
      if (ledSelect == 1001) {   // dedo 1 → servo1
        servo1.write(0);    // mueve servo1
        servo2.write(90);   // servo2 en reposo
        ledSeleccionado = -1; // no tocar LEDs
      }
      else if (ledSelect == 1002) { // dedo 2 → servo2
        servo2.write(180);  // mueve servo2
        servo1.write(90);   // servo1 en reposo
        ledSeleccionado = -1;
      }
      else {
        // --- Control de LEDs ---
        if (ledSelect == 0) { // apagar todos
          for (int i = 0; i < NUM; i++) {
            brilloLeds[i] = 0;
            analogWrite(leds[i], 0);
          }
          ledSeleccionado = -1;
        } 
        else if (ledSelect > 0 && ledSelect <= NUM) {
          int index = ledSelect - 1;
          if (brilloLeds[index] == 0) {
            brilloLeds[index] = 255;
            analogWrite(leds[index], 255);
          }
          ledSeleccionado = index;
        }

        // Mano izquierda ajusta brillo SOLO del LED seleccionado
        if (ledSeleccionado != -1 && nivelBrillo > 0) {
          brilloLeds[ledSeleccionado] = constrain(nivelBrillo, 0, 255);
          analogWrite(leds[ledSeleccionado], brilloLeds[ledSeleccionado]);
        }
      }
    }
  }
}
