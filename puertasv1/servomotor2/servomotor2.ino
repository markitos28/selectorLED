#define NUM 5
int leds[NUM] = {3, 5, 6, 9, 10}; // Pines PWM

int brilloLeds[NUM];   // guarda el brillo actual de cada LED
int ledSeleccionado = -1; // LED actualmente seleccionado para modificar brillo

void setup() {
  Serial.begin(9600);

  // Inicializar LEDs apagados
  for (int i = 0; i < NUM; i++) {
    pinMode(leds[i], OUTPUT);
    brilloLeds[i] = 0;
    analogWrite(leds[i], 0);
  }
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    int coma = input.indexOf(',');

    if (coma > 0) {
      int ledSelect = input.substring(0, coma).toInt();
      int nivelBrillo = input.substring(coma + 1).toInt();

      // --- Si mano derecha manda 0 → apagar todos ---
      if (ledSelect == 0) {
        for (int i = 0; i < NUM; i++) {
          brilloLeds[i] = 0;
          analogWrite(leds[i], 0);
        }
        ledSeleccionado = -1; // reset de selección
      } 
      // --- Si se selecciona un LED válido con mano derecha ---
      else if (ledSelect > 0 && ledSelect <= NUM) {
        int index = ledSelect - 1;
        // Si estaba apagado, prender al máximo
        if (brilloLeds[index] == 0) {
          brilloLeds[index] = 255;
          analogWrite(leds[index], 255);
        }
        // Guardar ese LED como seleccionado para ajuste de brillo
        ledSeleccionado = index;
      }

      // --- Mano izquierda controla el brillo SOLO del LED seleccionado ---
      if (ledSeleccionado != -1 && nivelBrillo > 0) {
        brilloLeds[ledSeleccionado] = constrain(nivelBrillo, 0, 255);
        analogWrite(leds[ledSeleccionado], brilloLeds[ledSeleccionado]);
      }
    }
  }
}