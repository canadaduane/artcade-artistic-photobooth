#include "Switch.h"

int counter = 0;

const int leftPin = 11;
const int rightPin = 15;
const int actionPin = 14;

Switch left = Switch(leftPin);
Switch right = Switch(rightPin);
Switch action = Switch(actionPin);

void setup() { }

uint32_t longPressedAt = 0;

void loop() {
  left.poll();
  if (left.pushed()) {
    Keyboard.set_key1(KEY_LEFT);
    Keyboard.send_now();
    Keyboard.set_key1(0);
    Keyboard.send_now();
  }

  right.poll();
  if (right.pushed()) {
    Keyboard.set_key1(KEY_RIGHT);
    Keyboard.send_now();
    Keyboard.set_key1(0);
    Keyboard.send_now();
  }

  action.poll();
  if (action.pushed()) {
    longPressedAt = millis() + 2000;
  }

  if (action.released()) {
    uint32_t now = millis();
    if (now >= longPressedAt) {
      Keyboard.set_key1(KEY_ENTER);
      Keyboard.send_now();
      Keyboard.set_key1(0);
      Keyboard.send_now();
    } else {
      Keyboard.set_key1(KEY_SPACE);
      Keyboard.send_now();
      Keyboard.set_key1(0);
      Keyboard.send_now();
    }
  }
}
