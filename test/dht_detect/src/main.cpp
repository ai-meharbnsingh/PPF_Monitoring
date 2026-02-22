// ─────────────────────────────────────────────────────────────────────────────
//  PPF Factory — Comprehensive Sensor Test
//  Tests ALL sensors from the PCB pin reference table:
//    GPIO5  → DHT11 / AM2305B  (tries both types)
//    GPIO0  → DS18B20 Bus 1    (OneWire)
//    GPIO17 → DS18B20 Bus 2    (OneWire)
//  Reboot ESP32 to re-run.
// ─────────────────────────────────────────────────────────────────────────────
#include <Arduino.h>
#include <DHT.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// ── PIN MAP (from PCB reference v3.5) ────────────────────────────────────────
#define PIN_DHT        5     // DHT11 / AM2305B
#define PIN_DS18B20_1  0     // DS18B20 Bus 1 (OneWire)
#define PIN_DS18B20_2  17    // DS18B20 Bus 2 (OneWire)
#define DHT_SAMPLES    5     // readings per DHT type
#define DHT_DELAY_MS   2300  // ms between DHT reads
// ─────────────────────────────────────────────────────────────────────────────

// ── Helpers ───────────────────────────────────────────────────────────────────
void sep()  { Serial.println("  ──────────────────────────────────────────────"); }
void sep2() { Serial.println("╠══════════════════════════════════════════════════════╣"); }

// ─────────────────────────────────────────────────────────────────────────────
//  DHT TEST  (GPIO5, tries DHT11 then DHT22/AM2305B)
// ─────────────────────────────────────────────────────────────────────────────
struct DHTResult {
    const char* label;
    int   valid;
    float avgTemp;
    float avgHum;
};

DHTResult testDHT(const char* label, uint8_t dhtType, uint8_t pin) {
    Serial.printf("  [%s] Testing on GPIO%d …\n", label, pin);
    DHT dht(pin, dhtType);
    dht.begin();
    delay(2000);

    int   valid = 0;
    float sumT = 0, sumH = 0;
    for (int i = 1; i <= DHT_SAMPLES; i++) {
        delay(DHT_DELAY_MS);
        float t = dht.readTemperature();
        float h = dht.readHumidity();
        bool  ok = !isnan(t) && !isnan(h);
        Serial.printf("    [%d/%d] %5.1f°C  %5.1f%%  %s\n",
                      i, DHT_SAMPLES, t, h, ok ? "✓" : "✗");
        if (ok) { valid++; sumT += t; sumH += h; }
    }
    DHTResult r;
    r.label   = label;
    r.valid   = valid;
    r.avgTemp = valid ? sumT / valid : NAN;
    r.avgHum  = valid ? sumH / valid : NAN;
    return r;
}

void runDHTSection() {
    Serial.println();
    Serial.println("╔══════════════════════════════════════════════════════╗");
    Serial.println("║  SENSOR 1 — DHT / AM2305B  on GPIO5                 ║");
    Serial.println("╚══════════════════════════════════════════════════════╝");

    DHTResult r11 = testDHT("DHT11",         DHT11, PIN_DHT);
    Serial.println();
    DHTResult r22 = testDHT("DHT22/AM2305B", DHT22, PIN_DHT);

    Serial.println();
    Serial.println("  ── Results ────────────────────────────────────────");
    Serial.printf( "  DHT11         : valid=%d/%d  avg=%.1f°C  %.1f%%\n",
                   r11.valid, DHT_SAMPLES, r11.avgTemp, r11.avgHum);
    Serial.printf( "  DHT22/AM2305B : valid=%d/%d  avg=%.1f°C  %.1f%%\n",
                   r22.valid, DHT_SAMPLES, r22.avgTemp, r22.avgHum);

    // Pick best
    DHTResult* best = nullptr;
    if      (r22.valid > 0 && r22.valid >= r11.valid) best = &r22;
    else if (r11.valid > 0)                            best = &r11;

    Serial.println();
    if (!best) {
        Serial.println("  ✗ VERDICT: NO DHT SENSOR DETECTED ON GPIO5");
        Serial.println("    Causes: missing 10kΩ pull-up, bad wiring, or 3.3V issue.");
    } else {
        Serial.printf( "  ✓ VERDICT: %s DETECTED ON GPIO5\n", best->label);
        Serial.printf( "    Avg temp=%.1f°C  avg hum=%.1f%%\n", best->avgTemp, best->avgHum);
        if (best == &r11)
            Serial.println("    → Firmware: use DHT11 type in sensors/dht22.cpp");
        else
            Serial.println("    → Firmware: DHT22/AM2305B ✓ SENSOR_CONFIG_DHT22 OK");
    }
}

// ─────────────────────────────────────────────────────────────────────────────
//  DS18B20 TEST  (OneWire bus scan)
// ─────────────────────────────────────────────────────────────────────────────
void runDS18B20Section(const char* busName, uint8_t pin) {
    Serial.println();
    Serial.printf("╔══════════════════════════════════════════════════════╗\n");
    Serial.printf("║  SENSOR — DS18B20  %s on GPIO%-2d%-19s║\n",
                  busName, pin, "");
    Serial.println("╚══════════════════════════════════════════════════════╝");

    OneWire           ow(pin);
    DallasTemperature sensors(&ow);

    sensors.begin();
    int count = sensors.getDeviceCount();
    Serial.printf("  Devices found on bus: %d\n", count);

    if (count == 0) {
        Serial.println("  ✗ NO DS18B20 FOUND");
        Serial.println("    Causes: missing 4.7kΩ pull-up on DATA line, bad wiring.");
        return;
    }

    sensors.requestTemperatures();
    delay(800);  // conversion time

    for (int i = 0; i < count; i++) {
        DeviceAddress addr;
        if (!sensors.getAddress(addr, i)) continue;

        // Print ROM address
        Serial.printf("  Device %d  ROM: ", i);
        for (int b = 0; b < 8; b++) Serial.printf("%02X ", addr[b]);
        Serial.println();

        float tempC = sensors.getTempC(addr);
        if (tempC == DEVICE_DISCONNECTED_C) {
            Serial.println("  ✗ Read failed (disconnected)");
        } else {
            Serial.printf("  ✓ Temperature: %.2f°C  (%.2f°F)\n",
                          tempC, DallasTemperature::toFahrenheit(tempC));
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
//  MAIN
// ─────────────────────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    delay(2000);

    Serial.println();
    Serial.println("╔══════════════════════════════════════════════════════╗");
    Serial.println("║       PPF FACTORY — COMPREHENSIVE SENSOR TEST       ║");
    Serial.println("╠══════════════════════════════════════════════════════╣");
    Serial.println("║  GPIO5  → DHT11 / AM2305B                           ║");
    Serial.println("║  GPIO0  → DS18B20 Bus 1 (OneWire)                   ║");
    Serial.println("║  GPIO17 → DS18B20 Bus 2 (OneWire)                   ║");
    Serial.println("╚══════════════════════════════════════════════════════╝");

    // 1. DHT / AM2305B
    runDHTSection();

    // 2. DS18B20 Bus 1
    runDS18B20Section("Bus 1", PIN_DS18B20_1);

    // 3. DS18B20 Bus 2
    runDS18B20Section("Bus 2", PIN_DS18B20_2);

    // ── Final Summary ─────────────────────────────────────────────────────────
    Serial.println();
    Serial.println("╔══════════════════════════════════════════════════════╗");
    Serial.println("║                  TEST COMPLETE                      ║");
    Serial.println("║  Reboot ESP32 to run again.                         ║");
    Serial.println("╚══════════════════════════════════════════════════════╝");
}

void loop() {}
