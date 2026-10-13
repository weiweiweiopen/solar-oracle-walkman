#include <Arduino.h>
#include "wifi_secrets.h"
#include <HTTPClient.h>
#include <WiFi.h>
#include <Wire.h>
#include <cstring>
#include <esp_system.h>
#include <esp_task_wdt.h>
#include <esp_wifi.h>

constexpr uint8_t DSSC_PIN = 3; // A: preserve historical channel
constexpr uint8_t DSSC_B_PIN = 2; // ESP32-C3 ADC1_CH2, input only
constexpr uint8_t SDA_PIN = 8;
constexpr uint8_t SCL_PIN = 9;
constexpr uint8_t BH1750_ADDRESS = 0x23;
constexpr uint8_t SHT20_ADDRESS = 0x40;
constexpr uint8_t BMP180_ADDRESS = 0x77;
constexpr size_t SAMPLE_COUNT = 64;
constexpr uint32_t REPORT_INTERVAL_MS = 300000;
constexpr uint32_t POST_RETRY_MS = 30000;
constexpr uint32_t WIFI_CONNECT_TIMEOUT_MS = 15000;
constexpr uint32_t WIFI_RETRY_INITIAL_MS = 5000;
constexpr uint32_t WIFI_RETRY_MAX_MS = 60000;
constexpr uint32_t OFFLINE_RESTART_MS = 180000;
constexpr uint32_t RTC_STATE_MAGIC = 0x44535343;
constexpr uint32_t RTC_STATE_MAGIC_INVERSE = ~RTC_STATE_MAGIC;
constexpr uint32_t RTC_STATE_VERSION = 1;
constexpr uint32_t RESTART_MARKER_OFFLINE = 1;



static const char *RECEIVER_URLS[] = {
  "http://192.168.1.102:8787/readings",
  "http://Mac-mini.local:8787/readings"
};


struct FailureSnapshot {
  uint32_t marker;
  uint32_t uptimeSeconds;
  uint32_t wifiAttempts;
  int32_t httpCode;
  int32_t rssi;
  uint8_t disconnectReason;
};

struct PersistentRtcState {
  uint32_t magic;
  uint32_t magicInverse;
  uint32_t version;
  uint32_t offlineRestartUsed;
  FailureSnapshot snapshot;
  uint32_t checksum;
};

RTC_NOINIT_ATTR PersistentRtcState rtcState;
static FailureSnapshot bootFailureSnapshot = {};
static unsigned long lastSuccessfulReport = 0;
static unsigned long lastPostAttempt = 0;
static unsigned long lastWifiAttempt = 0;
static unsigned long offlineSince = 0;
static uint32_t wifiRetryMs = WIFI_RETRY_INITIAL_MS;
static uint32_t wifiAttemptCount = 0;
static uint32_t reportSequence = 0;
static uint32_t bootId = 0;
static esp_reset_reason_t bootResetReason = ESP_RST_UNKNOWN;
static volatile uint8_t lastDisconnectReason = 0;
static uint8_t consecutivePostFailures = 0;
static int lastHttpCode = 0;
static bool reportPending = true;
static bool postAttempted = false;
static bool wifiAttempted = false;

uint32_t rtcStateChecksum(const PersistentRtcState &state) {
  const auto *bytes = reinterpret_cast<const uint8_t *>(&state);
  uint32_t hash = 2166136261UL;
  for (size_t i = 0; i < sizeof(PersistentRtcState) - sizeof(state.checksum); ++i) {
    hash = (hash ^ bytes[i]) * 16777619UL;
  }
  return hash;
}

void saveRtcState() {
  rtcState.checksum = rtcStateChecksum(rtcState);
}

bool rtcStateIsValid() {
  return rtcState.magic == RTC_STATE_MAGIC
    && rtcState.magicInverse == RTC_STATE_MAGIC_INVERSE
    && rtcState.version == RTC_STATE_VERSION
    && rtcState.offlineRestartUsed <= 1
    && rtcState.checksum == rtcStateChecksum(rtcState);
}

void resetRtcState() {
  memset(&rtcState, 0, sizeof(rtcState));
  rtcState.magic = RTC_STATE_MAGIC;
  rtcState.magicInverse = RTC_STATE_MAGIC_INVERSE;
  rtcState.version = RTC_STATE_VERSION;
  saveRtcState();
}

const char *resetReasonName(esp_reset_reason_t reason) {
  switch (reason) {
    case ESP_RST_POWERON: return "power_on";
    case ESP_RST_EXT: return "external";
    case ESP_RST_SW: return "software";
    case ESP_RST_PANIC: return "panic";
    case ESP_RST_INT_WDT: return "interrupt_watchdog";
    case ESP_RST_TASK_WDT: return "task_watchdog";
    case ESP_RST_WDT: return "watchdog";
    case ESP_RST_DEEPSLEEP: return "deep_sleep";
    case ESP_RST_BROWNOUT: return "brownout";
    case ESP_RST_SDIO: return "sdio";
    default: return "unknown";
  }
}

void onWiFiEvent(WiFiEvent_t event, WiFiEventInfo_t info) {
  if (event != ARDUINO_EVENT_WIFI_STA_DISCONNECTED) return;
  const uint8_t reason = info.wifi_sta_disconnected.reason;
  if (reason != WIFI_REASON_ASSOC_LEAVE) lastDisconnectReason = reason;
}

void restartDevice(uint32_t marker, const char *message) {
  rtcState.snapshot.marker = marker;
  rtcState.snapshot.uptimeSeconds = millis() / 1000UL;
  rtcState.snapshot.wifiAttempts = wifiAttemptCount;
  rtcState.snapshot.httpCode = lastHttpCode;
  rtcState.snapshot.rssi = WiFi.status() == WL_CONNECTED ? WiFi.RSSI() : 0;
  rtcState.snapshot.disconnectReason = lastDisconnectReason;
  saveRtcState();
  Serial.println(message);
  Serial.flush();
  delay(100);
  ESP.restart();
}

uint16_t read16(uint8_t address, uint8_t reg) {
  Wire.beginTransmission(address); Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return 0xFFFF;
  if (Wire.requestFrom(address, static_cast<uint8_t>(2)) != 2) return 0xFFFF;
  return (static_cast<uint16_t>(Wire.read()) << 8) | Wire.read();
}

bool write8(uint8_t address, uint8_t reg, uint8_t value) {
  Wire.beginTransmission(address); Wire.write(reg); Wire.write(value);
  return Wire.endTransmission() == 0;
}

bool readSht20(float &temperatureC, float &humidityPct) {
  Wire.beginTransmission(SHT20_ADDRESS); Wire.write(0xF3);
  if (Wire.endTransmission() != 0) return false;
  delay(90);
  if (Wire.requestFrom(SHT20_ADDRESS, static_cast<uint8_t>(3)) < 2) return false;
  uint16_t rawTemperature = (static_cast<uint16_t>(Wire.read()) << 8) | Wire.read();
  while (Wire.available()) Wire.read();
  rawTemperature &= 0xFFFC;
  temperatureC = -46.85f + 175.72f * rawTemperature / 65536.0f;

  Wire.beginTransmission(SHT20_ADDRESS); Wire.write(0xF5);
  if (Wire.endTransmission() != 0) return false;
  delay(35);
  if (Wire.requestFrom(SHT20_ADDRESS, static_cast<uint8_t>(3)) < 2) return false;
  uint16_t rawHumidity = (static_cast<uint16_t>(Wire.read()) << 8) | Wire.read();
  while (Wire.available()) Wire.read();
  rawHumidity &= 0xFFFC;
  humidityPct = constrain(-6.0f + 125.0f * rawHumidity / 65536.0f, 0.0f, 100.0f);
  return true;
}

bool readBh1750(float &lux) {
  Wire.beginTransmission(BH1750_ADDRESS); Wire.write(0x20);
  if (Wire.endTransmission() != 0) return false;
  delay(180);
  if (Wire.requestFrom(BH1750_ADDRESS, static_cast<uint8_t>(2)) != 2) return false;
  uint16_t raw = (static_cast<uint16_t>(Wire.read()) << 8) | Wire.read();
  lux = raw / 1.2f;
  return true;
}

bool readBmp180(float &pressureHpa) {
  const int16_t ac1 = static_cast<int16_t>(read16(BMP180_ADDRESS, 0xAA));
  const int16_t ac2 = static_cast<int16_t>(read16(BMP180_ADDRESS, 0xAC));
  const int16_t ac3 = static_cast<int16_t>(read16(BMP180_ADDRESS, 0xAE));
  const uint16_t ac4 = read16(BMP180_ADDRESS, 0xB0);
  const uint16_t ac5 = read16(BMP180_ADDRESS, 0xB2);
  const uint16_t ac6 = read16(BMP180_ADDRESS, 0xB4);
  const int16_t b1 = static_cast<int16_t>(read16(BMP180_ADDRESS, 0xB6));
  const int16_t b2 = static_cast<int16_t>(read16(BMP180_ADDRESS, 0xB8));
  const int16_t mc = static_cast<int16_t>(read16(BMP180_ADDRESS, 0xBC));
  const int16_t md = static_cast<int16_t>(read16(BMP180_ADDRESS, 0xBE));
  if (ac4 == 0xFFFF || ac5 == 0xFFFF || ac6 == 0xFFFF) return false;

  if (!write8(BMP180_ADDRESS, 0xF4, 0x2E)) return false;
  delay(5);
  const int32_t ut = read16(BMP180_ADDRESS, 0xF6);
  int32_t x1 = ((ut - ac6) * static_cast<int32_t>(ac5)) >> 15;
  if (x1 + md == 0) return false;
  int32_t x2 = (static_cast<int32_t>(mc) << 11) / (x1 + md);
  const int32_t b5 = x1 + x2;

  if (!write8(BMP180_ADDRESS, 0xF4, 0x34)) return false;
  delay(5);
  Wire.beginTransmission(BMP180_ADDRESS); Wire.write(0xF6);
  if (Wire.endTransmission(false) != 0 || Wire.requestFrom(BMP180_ADDRESS, static_cast<uint8_t>(3)) != 3) return false;
  const int32_t up = ((static_cast<uint32_t>(Wire.read()) << 16) |
                      (static_cast<uint32_t>(Wire.read()) << 8) | Wire.read()) >> 8;
  const int32_t b6 = b5 - 4000;
  x1 = (static_cast<int32_t>(b2) * ((b6 * b6) >> 12)) >> 11;
  x2 = (static_cast<int32_t>(ac2) * b6) >> 11;
  int32_t x3 = x1 + x2;
  const int32_t b3 = ((static_cast<int32_t>(ac1) * 4 + x3) + 2) / 4;
  x1 = (static_cast<int32_t>(ac3) * b6) >> 13;
  x2 = (static_cast<int32_t>(b1) * ((b6 * b6) >> 12)) >> 16;
  x3 = (x1 + x2 + 2) >> 2;
  const uint32_t b4 = (static_cast<uint32_t>(ac4) * (x3 + 32768)) >> 15;
  if (b4 == 0 || up < b3) return false;
  const uint32_t b7 = static_cast<uint32_t>(up - b3) * 50000;
  int32_t pressurePa = b7 < 0x80000000UL ? (b7 * 2) / b4 : (b7 / b4) * 2;
  x1 = (pressurePa >> 8) * (pressurePa >> 8);
  x1 = (x1 * 3038) >> 16;
  x2 = (-7357 * pressurePa) >> 16;
  pressurePa += (x1 + x2 + 3791) >> 4;
  pressureHpa = pressurePa / 100.0f;
  return true;
}

String jsonNumber(float value, uint8_t decimals) {
  return isnan(value) ? "null" : String(value, static_cast<unsigned int>(decimals));
}

bool connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return true;
  wifiAttempted = true;
  ++wifiAttemptCount;
  WiFi.setTxPower(WIFI_POWER_15dBm);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  const unsigned long started = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - started < WIFI_CONNECT_TIMEOUT_MS) {
    esp_task_wdt_reset();
    delay(100);
  }
  lastWifiAttempt = millis();
  if (WiFi.status() != WL_CONNECTED) {
    if (offlineSince == 0) offlineSince = millis();
    wifiRetryMs = wifiRetryMs < WIFI_RETRY_MAX_MS / 2
      ? wifiRetryMs * 2 : WIFI_RETRY_MAX_MS;
    Serial.printf("WiFi failed status=%d reason=%u retry_ms=%lu\n",
                  WiFi.status(), lastDisconnectReason,
                  static_cast<unsigned long>(wifiRetryMs));
    return false;
  }
  offlineSince = 0;
  wifiRetryMs = WIFI_RETRY_INITIAL_MS;
  if (rtcState.offlineRestartUsed != 0) {
    rtcState.offlineRestartUsed = 0;
    saveRtcState();
  }
  Serial.printf("WiFi connected ip=%s rssi=%d tx=15dBm\n",
                WiFi.localIP().toString().c_str(), WiFi.RSSI());
  return true;
}

void serviceWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    offlineSince = 0;
    wifiRetryMs = WIFI_RETRY_INITIAL_MS;
    return;
  }
  if (offlineSince == 0) offlineSince = millis();
  if (!wifiAttempted || millis() - lastWifiAttempt >= wifiRetryMs) connectWiFi();
  if (WiFi.status() != WL_CONNECTED && offlineSince != 0
      && millis() - offlineSince >= OFFLINE_RESTART_MS
      && rtcState.offlineRestartUsed == 0) {
    rtcState.offlineRestartUsed = 1;
    restartDevice(RESTART_MARKER_OFFLINE, "Restarting after prolonged WiFi outage");
  }
}

bool sendReading() {
  float rawSum = 0, millivoltSum = 0;
  for (size_t i = 0; i < SAMPLE_COUNT; ++i) {
    rawSum += analogRead(DSSC_PIN);
    millivoltSum += analogReadMilliVolts(DSSC_PIN);
    delayMicroseconds(1000);
  }
  const float raw = rawSum / SAMPLE_COUNT;
  const float millivolts = millivoltSum / SAMPLE_COUNT;
  float rawBSum = 0, millivoltBSum = 0;
  for (size_t i = 0; i < SAMPLE_COUNT; ++i) {
    rawBSum += analogRead(DSSC_B_PIN);
    millivoltBSum += analogReadMilliVolts(DSSC_B_PIN);
    delayMicroseconds(1000);
  }
  const float rawB = rawBSum / SAMPLE_COUNT;
  const float millivoltsB = millivoltBSum / SAMPLE_COUNT;
  float temperature = NAN, humidity = NAN, pressure = NAN, light = NAN;
  readSht20(temperature, humidity);
  readBmp180(pressure);
  readBh1750(light);
  const float mcuTemperature = temperatureRead();

  String body = "{\"raw\":" + String(raw, 1)
    + ",\"voltage_mV\":" + String(millivolts, 1)
    + ",\"voltage_V\":" + String(millivolts / 1000.0f, 4)
    + ",\"ambient_temp_C\":" + jsonNumber(temperature, 2)
    + ",\"humidity_pct\":" + jsonNumber(humidity, 2)
    + ",\"pressure_hPa\":" + jsonNumber(pressure, 2)
    + ",\"lux\":" + jsonNumber(light, 1)
    + ",\"mcu_temp_C\":" + jsonNumber(mcuTemperature, 1)
    + ",\"boot_id\":" + String(bootId)
    + ",\"report_sequence\":" + String(reportSequence)
    + ",\"uptime_s\":" + String(millis() / 1000UL)
    + ",\"reset_reason\":\"" + resetReasonName(bootResetReason) + "\""
    + ",\"restart_marker\":" + String(bootFailureSnapshot.marker)
    + ",\"prior_disconnect_reason\":" + String(bootFailureSnapshot.disconnectReason)
    + ",\"prior_http_code\":" + String(bootFailureSnapshot.httpCode)
    + ",\"prior_rssi_dBm\":" + String(bootFailureSnapshot.rssi)
    + ",\"prior_uptime_s\":" + String(bootFailureSnapshot.uptimeSeconds)
    + ",\"prior_wifi_attempts\":" + String(bootFailureSnapshot.wifiAttempts)
    + ",\"wifi_rssi_dBm\":" + String(WiFi.RSSI())
    + ",\"wifi_attempts\":" + String(wifiAttemptCount)
    + ",\"last_disconnect_reason\":" + String(lastDisconnectReason)
    + ",\"previous_http_code\":" + String(lastHttpCode)
    + ",\"free_heap_B\":" + String(ESP.getFreeHeap()) + "}";
  // Top-level voltage remains A for backward-compatible receivers.
  body.remove(body.length() - 1);
  body += ",\"schema_version\":2,\"device_id\":\"esp32c3-64e833b913b8\""
    ",\"sample_id\":\"green_proofs_are_not_always_about_tax_write-offs_1\",\"gpio\":3"
    ",\"channels\":[{\"sample_id\":\"dssc_55x55_b\",\"gpio\":2,\"raw\":" + String(rawB, 1)
    + ",\"voltage_mV\":" + String(millivoltsB, 1)
    + ",\"voltage_V\":" + String(millivoltsB / 1000.0f, 4) + "}]}";
  Serial.println(body);

  if (WiFi.status() != WL_CONNECTED) return false;
  for (const char *url : RECEIVER_URLS) {
    WiFiClient client;
    HTTPClient http;
    http.setConnectTimeout(5000);
    http.setTimeout(5000);
    if (!http.begin(client, url)) {
      lastHttpCode = -1000;
      continue;
    }
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-DSSC-Token", TOKEN);
    const int code = http.POST(body);
    lastHttpCode = code;
    Serial.printf("POST %s code=%d\n", url, code);
    http.end();
    if (code >= 200 && code < 300) return true;
  }
  return false;
}

void setup() {
  Serial.begin(115200);
  bootResetReason = esp_reset_reason();
  const bool warmReset = bootResetReason == ESP_RST_SW
    || bootResetReason == ESP_RST_PANIC
    || bootResetReason == ESP_RST_INT_WDT
    || bootResetReason == ESP_RST_TASK_WDT
    || bootResetReason == ESP_RST_WDT;
  if (!warmReset || !rtcStateIsValid()) resetRtcState();
  if (rtcState.snapshot.marker != 0) {
    bootFailureSnapshot = rtcState.snapshot;
  }
  memset(&rtcState.snapshot, 0, sizeof(rtcState.snapshot));
  saveRtcState();
  bootId = esp_random();
  esp_task_wdt_init(60, true);
  esp_task_wdt_add(nullptr);
  Wire.begin(SDA_PIN, SCL_PIN);
  pinMode(DSSC_PIN, INPUT);
  pinMode(DSSC_B_PIN, INPUT);
  analogReadResolution(12);
  analogSetPinAttenuation(DSSC_PIN, ADC_2_5db);
  analogSetPinAttenuation(DSSC_B_PIN, ADC_2_5db);
  WiFi.mode(WIFI_STA);
  WiFi.persistent(false);
  WiFi.setAutoReconnect(false);
  WiFi.setSleep(false);
  WiFi.onEvent(onWiFiEvent);
  esp_wifi_set_bandwidth(WIFI_IF_STA, WIFI_BW_HT20);
  delay(800);
  offlineSince = millis();
  connectWiFi();
}

void loop() {
  esp_task_wdt_reset();
  serviceWiFi();

  if (!reportPending && millis() - lastSuccessfulReport >= REPORT_INTERVAL_MS) {
    reportPending = true;
    postAttempted = false;
  }

  if (reportPending && WiFi.status() == WL_CONNECTED
      && (!postAttempted || millis() - lastPostAttempt >= POST_RETRY_MS)) {
    if (!postAttempted) ++reportSequence;
    postAttempted = true;
    lastPostAttempt = millis();
    if (sendReading()) {
      consecutivePostFailures = 0;
      reportPending = false;
      postAttempted = false;
      lastSuccessfulReport = millis();
    } else {
      ++consecutivePostFailures;
      Serial.printf("Upload failed count=%u code=%d; WiFi link left untouched\n",
                    consecutivePostFailures, lastHttpCode);
    }
  }

  esp_task_wdt_reset();
  delay(250);
}
