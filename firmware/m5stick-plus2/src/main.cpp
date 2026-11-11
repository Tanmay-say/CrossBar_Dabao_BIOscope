#include <M5Unified.h>
#include <ArduinoJson.h>

// Protocol preparation only: no firmware has been flashed to a physical device.
// USB serial frames are newline-delimited JSON; requests carry protocol/version fields.
static const char *experiments[] = {"bio-smoke", "register-inspection", "blink"};
static int selected = 0;
static String rx;
static String hostState = "Waiting for BIOScope host";
static String resultState = "No run yet";
static unsigned long lastHello = 0;

void drawUi() {
  M5.Display.fillScreen(TFT_BLACK); M5.Display.setTextColor(TFT_CYAN, TFT_BLACK);
  M5.Display.setTextSize(2); M5.Display.setCursor(8, 8); M5.Display.println("BIOScope");
  M5.Display.drawFastHLine(8, 34, 220, TFT_DARKGREY);
  M5.Display.setTextSize(1); M5.Display.setTextColor(TFT_WHITE, TFT_BLACK);
  M5.Display.setCursor(8, 46); M5.Display.println("Host link");
  M5.Display.setTextColor(hostState.startsWith("Connected") ? TFT_GREEN : TFT_ORANGE, TFT_BLACK);
  M5.Display.setCursor(8, 60); M5.Display.println(hostState);
  M5.Display.setTextColor(TFT_WHITE, TFT_BLACK); M5.Display.setCursor(8, 86); M5.Display.println("Experiment");
  M5.Display.setTextColor(TFT_CYAN, TFT_BLACK); M5.Display.setCursor(8, 101); M5.Display.println(experiments[selected]);
  M5.Display.setTextColor(TFT_WHITE, TFT_BLACK); M5.Display.setCursor(8, 130); M5.Display.println(resultState);
  M5.Display.setTextColor(TFT_DARKGREY, TFT_BLACK); M5.Display.setCursor(8, 215); M5.Display.println("A/B select   C run");
}

void handleFrame(const String &line) {
  JsonDocument doc; if (deserializeJson(doc, line)) return;
  const char *type = doc["type"] | "";
  if (!strcmp(type, "hello_ack") && (doc["protocol"] | 0) == 1) hostState = "Connected · v1";
  else if (!strcmp(type, "run_status")) resultState = String((const char *)(doc["state"] | "Unknown"));
  else if (!strcmp(type, "run_result")) resultState = String((const char *)(doc["result"] | "Complete"));
  else if (!strcmp(type, "error")) resultState = String("Error: ") + (const char *)(doc["message"] | "unknown");
  drawUi();
}

void setup() {
  auto cfg = M5.config(); M5.begin(cfg); Serial.begin(115200); M5.Display.setRotation(1); drawUi();
}
void loop() {
  M5.update();
  if (M5.BtnA.wasPressed()) { selected = (selected + 2) % 3; drawUi(); }
  if (M5.BtnB.wasPressed()) { selected = (selected + 1) % 3; drawUi(); }
  if (M5.BtnC.wasPressed()) {
    JsonDocument msg; msg["type"]="run_request"; msg["protocol"]=1; msg["experiment_id"]=experiments[selected];
    msg["mode"]="SIMULATION"; serializeJson(msg, Serial); Serial.println(); resultState="Run requested"; drawUi();
  }
  while (Serial.available()) { char c=Serial.read(); if(c=='\n') { handleFrame(rx); rx=""; } else if(rx.length()<1024) rx+=c; else rx=""; }
  if (millis()-lastHello>1000) { JsonDocument msg; msg["type"]="hello"; msg["protocol"]=1; serializeJson(msg,Serial); Serial.println(); lastHello=millis(); }
  delay(10);
}
