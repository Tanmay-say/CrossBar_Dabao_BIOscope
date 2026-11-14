#include <M5Unified.h>
#include <ArduinoJson.h>
#include <driver/gpio.h>
#include <esp_timer.h>
#include <math.h>

// PulseLink receiver wiring: Plus2 Grove yellow = GPIO32, black = GND.
// Grove 5 V is never used. GPIO32 is not shared with the LCD, keys, mic or IMU.
static constexpr gpio_num_t SIGNAL_PIN = GPIO_NUM_32;
static constexpr uint8_t EXPECTED_RISING_EDGES = 10;
static constexpr uint32_t TELEMETRY_PERIOD_MS = 100;
static constexpr uint32_t WAITING_TIMEOUT_MS = 1500;
static constexpr uint8_t EDGE_QUEUE_SIZE = 16;

struct EdgeEvent { uint32_t timestamp_us; uint8_t level; };
static EdgeEvent edgeQueue[EDGE_QUEUE_SIZE];
static volatile uint8_t edgeHead = 0, edgeTail = 0;
static volatile uint32_t pulseCount = 0;
static volatile uint32_t lastRiseUs = 0;
static volatile uint32_t measuredPeriodUs = 0;
static volatile bool hasPeriod = false;
static volatile bool edgeOverflow = false;
static uint32_t sequenceNumber = 0;
static uint32_t lastTelemetryMs = 0;
static uint32_t lastEdgeSeenMs = 0;
static uint8_t displayPage = 0;
static String stateText = "waiting";
static String connectionText = "host heartbeat missing";
static String serialRx;
static uint32_t lastHostHeartbeatMs = 0;
static uint8_t latestLevel = 0;
static uint32_t latestCount = 0;
static float latestFrequency = NAN;
static uint32_t edgesSent = 0;

void IRAM_ATTR onSignalChange() {
  const uint8_t level = (uint8_t)gpio_get_level(SIGNAL_PIN);
  const uint32_t stamp = micros();
  const uint8_t next = (uint8_t)((edgeHead + 1) % EDGE_QUEUE_SIZE);
  if (next == edgeTail) {
    edgeOverflow = true;
    return;
  }
  edgeQueue[edgeHead].timestamp_us = stamp;
  edgeQueue[edgeHead].level = level;
  edgeHead = next;
  if (level) {
    if (pulseCount && lastRiseUs) {
      measuredPeriodUs = stamp - lastRiseUs; // unsigned subtraction handles micros() wrap
      hasPeriod = measuredPeriodUs != 0;
    }
    lastRiseUs = stamp;
    ++pulseCount;
  }
}

static uint8_t drainEdges(EdgeEvent *out, uint8_t capacity) {
  uint8_t count = 0;
  noInterrupts();
  while (edgeTail != edgeHead && count < capacity) {
    out[count].timestamp_us = edgeQueue[edgeTail].timestamp_us;
    out[count].level = edgeQueue[edgeTail].level;
    ++count;
    edgeTail = (uint8_t)((edgeTail + 1) % EDGE_QUEUE_SIZE);
  }
  interrupts();
  return count;
}

static void drawScreen() {
  M5.Display.fillScreen(TFT_BLACK);
  M5.Display.setTextSize(2);
  M5.Display.setTextColor(TFT_CYAN, TFT_BLACK);
  M5.Display.setCursor(7, 5);
  M5.Display.println("PulseLink");
  M5.Display.drawFastHLine(7, 29, 226, TFT_DARKGREY);
  M5.Display.setTextSize(1);
  M5.Display.setTextColor(TFT_WHITE, TFT_BLACK);
  M5.Display.setCursor(8, 36);
  M5.Display.printf("USB: %s", connectionText.c_str());
  M5.Display.setCursor(8, 55);
  const char *displayState = stateText == "waiting" ? "WAITING" :
                             stateText == "measuring" ? "SIGNAL DETECTED" :
                             stateText == "complete" ? "COMPLETE" : "SIGNAL TIMEOUT";
  M5.Display.printf("STATE: %s", displayState);
  M5.Display.setCursor(8, 73);
  if (displayPage == 0) {
    M5.Display.printf("Rising pulses: %lu / %u", (unsigned long)latestCount, EXPECTED_RISING_EDGES);
    M5.Display.setCursor(8, 91);
    if (isnan(latestFrequency)) M5.Display.print("Frequency: waiting for 2 edges");
    else M5.Display.printf("Frequency: %.3f Hz", latestFrequency);
    M5.Display.setCursor(8, 109);
    M5.Display.printf("GPIO32 level: %u", latestLevel);
  } else {
    M5.Display.printf("Capture events: %lu", (unsigned long)edgesSent);
    M5.Display.setCursor(8, 91);
    M5.Display.print("Edge times: micros() timestamps");
    M5.Display.setCursor(8, 109);
    M5.Display.printf("GPIO32 level: %u", latestLevel);
  }
  M5.Display.setTextColor(TFT_DARKGREY, TFT_BLACK);
  M5.Display.setCursor(8, 127);
  M5.Display.print("A reset  B page");
}

static void resetMeasurement() {
  noInterrupts();
  edgeHead = edgeTail = 0;
  pulseCount = 0;
  lastRiseUs = 0;
  measuredPeriodUs = 0;
  hasPeriod = false;
  edgeOverflow = false;
  interrupts();
  latestCount = 0;
  latestFrequency = NAN;
  latestLevel = (uint8_t)gpio_get_level(SIGNAL_PIN);
  stateText = "waiting";
  lastEdgeSeenMs = millis();
  edgesSent = 0;
}

static void sendTelemetry() {
  EdgeEvent events[EDGE_QUEUE_SIZE - 1];
  const uint8_t n = drainEdges(events, EDGE_QUEUE_SIZE - 1);
  uint32_t count, period;
  bool validPeriod, overflow;
  noInterrupts();
  count = pulseCount;
  period = measuredPeriodUs;
  validPeriod = hasPeriod;
  overflow = edgeOverflow;
  interrupts();

  latestCount = count;
  latestLevel = (uint8_t)gpio_get_level(SIGNAL_PIN);
  if (validPeriod && period) latestFrequency = 1000000.0f / (float)period;
  const uint32_t now = millis();
  if (n) lastEdgeSeenMs = now;
  if (count >= EXPECTED_RISING_EDGES && latestLevel == 0) stateText = "complete";
  else if (count) stateText = (now - lastEdgeSeenMs > WAITING_TIMEOUT_MS) ? "timeout" : "measuring";
  else stateText = "waiting";

  JsonDocument doc;
  doc["protocol"] = 1;
  doc["device"] = "m5stick-pulse-link";
  doc["type"] = "telemetry";
  doc["sequence"] = sequenceNumber++;
  doc["state"] = stateText;
  doc["pulse_count"] = count;
  if (validPeriod && period) doc["frequency_hz"] = latestFrequency;
  else doc["frequency_hz"] = nullptr;
  doc["signal_level"] = latestLevel;
  doc["uptime_us"] = (uint64_t)esp_timer_get_time();
  doc["edge_overflow"] = overflow;
  JsonArray edges = doc["edges"].to<JsonArray>();
  for (uint8_t i = 0; i < n; ++i) {
    JsonObject edge = edges.add<JsonObject>();
    edge["timestamp_us"] = events[i].timestamp_us;
    edge["level"] = events[i].level;
    ++edgesSent;
  }
  serializeJson(doc, Serial);
  Serial.println();
}

void setup() {
  auto cfg = M5.config();
  M5.begin(cfg);
  M5.Display.setRotation(1);
  Serial.begin(115200);
  pinMode((int)SIGNAL_PIN, INPUT_PULLDOWN);
  attachInterrupt(digitalPinToInterrupt((int)SIGNAL_PIN), onSignalChange, CHANGE);
  resetMeasurement();
  drawScreen();
  Serial.println("{\"protocol\":1,\"device\":\"m5stick-pulse-link\",\"type\":\"hello\",\"firmware\":\"bioscope-pulselink/1\"}");
}

static void receiveHostHeartbeat() {
  while (Serial.available()) {
    const char c = (char)Serial.read();
    if (c == '\n') {
      JsonDocument doc;
      if (!deserializeJson(doc, serialRx) && doc.size() == 2 &&
          (doc["protocol"] | 0) == 1 && String((const char *)(doc["type"] | "")) == "host_heartbeat") {
        lastHostHeartbeatMs = millis();
      }
      serialRx = "";
    } else if (serialRx.length() < 128) {
      serialRx += c;
    } else {
      serialRx = ""; // bounded parser; unknown or oversized frames are ignored
    }
  }
}

void loop() {
  M5.update();
  if (M5.BtnA.wasPressed()) { resetMeasurement(); drawScreen(); }
  if (M5.BtnB.wasPressed()) { displayPage ^= 1; drawScreen(); }

  const uint32_t now = millis();
  connectionText = (lastHostHeartbeatMs && now - lastHostHeartbeatMs < 2500) ? "HOST CONNECTED" : "HOST DISCONNECTED";
  receiveHostHeartbeat();
  if (now - lastTelemetryMs >= TELEMETRY_PERIOD_MS) {
    lastTelemetryMs = now;
    sendTelemetry();
    drawScreen();
  }
  // A host disconnect does not stop edge capture or the local display. USB serial
  // is output-only for telemetry; a detached host cannot inject experiment commands.
  delay(2);
}
