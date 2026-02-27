/**
 * PMS5003 Sensor Test
 *
 * Standalone sketch to verify PMS5003 particulate matter sensor is wired
 * correctly and returning valid data over UART (Serial2).
 *
 * Wiring:
 *   PMS5003 TX  → ESP32 GPIO5   (Serial2 RX — ESP32 receives data)
 *   PMS5003 RX  → ESP32 GPIO33  (Serial2 TX — ESP32 sends commands)
 *   PMS5003 VCC → 5V
 *   PMS5003 GND → GND
 *   PMS5003 SET → 5V (or leave floating — active high)
 *
 * Protocol: 9600 baud, 8N1
 * Frame: 32 bytes starting with 0x42 0x4D
 *
 * The sensor needs ~30 seconds warm-up after power-on for the laser/fan
 * to stabilise. This sketch waits for that, then reads continuously.
 */

#include <Arduino.h>

// ─── Pin definitions ────────────────────────────────────────────────────────
#define PMS_RX_PIN   5    // ESP32 RX ← PMS5003 TX
#define PMS_TX_PIN   33   // ESP32 TX → PMS5003 RX
#define PMS_BAUD     9600

// ─── Frame constants ────────────────────────────────────────────────────────
#define PMS_FRAME_LEN    32
#define PMS_START_BYTE_1 0x42
#define PMS_START_BYTE_2 0x4D
#define PMS_TIMEOUT_MS   3000   // Timeout waiting for a frame
#define PMS_WARMUP_MS    30000  // 30 seconds warm-up

// ─── Globals ────────────────────────────────────────────────────────────────
unsigned long readCount   = 0;
unsigned long successCount = 0;
unsigned long failCount    = 0;

// ─── Read one 32-byte frame from Serial2 ────────────────────────────────────
// Returns true if a valid frame was read and checksum passes
bool readPMSFrame(uint8_t* buf) {
    uint32_t deadline = millis() + PMS_TIMEOUT_MS;

    // 1. Sync: find start bytes 0x42 0x4D
    uint8_t prev = 0;
    bool synced = false;
    while (millis() < deadline) {
        if (!Serial2.available()) {
            delay(1);
            continue;
        }
        uint8_t b = (uint8_t)Serial2.read();
        if (prev == PMS_START_BYTE_1 && b == PMS_START_BYTE_2) {
            buf[0] = PMS_START_BYTE_1;
            buf[1] = PMS_START_BYTE_2;
            synced = true;
            break;
        }
        prev = b;
    }

    if (!synced) {
        Serial.println("[PMS5003] Timeout waiting for start bytes (0x42 0x4D)");
        return false;
    }

    // 2. Read remaining 30 bytes
    uint8_t idx = 2;
    while (idx < PMS_FRAME_LEN && millis() < deadline) {
        if (Serial2.available()) {
            buf[idx++] = (uint8_t)Serial2.read();
        } else {
            delay(1);
        }
    }

    if (idx < PMS_FRAME_LEN) {
        Serial.printf("[PMS5003] Timeout reading frame body (got %d/%d bytes)\n",
                      idx, PMS_FRAME_LEN);
        return false;
    }

    // 3. Verify checksum: sum of bytes[0..29] == uint16 at bytes[30..31]
    uint16_t calcSum = 0;
    for (uint8_t i = 0; i < 30; i++) calcSum += buf[i];
    uint16_t frameSum = ((uint16_t)buf[30] << 8) | buf[31];

    if (calcSum != frameSum) {
        Serial.printf("[PMS5003] Checksum FAIL — calc=0x%04X  frame=0x%04X\n",
                      calcSum, frameSum);
        return false;
    }

    return true;
}

// ─── Parse and display a valid frame ────────────────────────────────────────
void displayFrame(const uint8_t* buf) {
    // Helper: combine two bytes into uint16 (big-endian)
    auto b16 = [&](uint8_t i) -> uint16_t {
        return ((uint16_t)buf[i] << 8) | buf[i + 1];
    };

    // CF=1 standard particle (factory calibration)
    uint16_t pm1_cf   = b16(4);
    uint16_t pm25_cf  = b16(6);
    uint16_t pm10_cf  = b16(8);

    // Atmospheric environment values (what you normally report)
    uint16_t pm1_atm  = b16(10);
    uint16_t pm25_atm = b16(12);
    uint16_t pm10_atm = b16(14);

    // Particle counts per 0.1 L of air
    uint16_t p03  = b16(16);
    uint16_t p05  = b16(18);
    uint16_t p10  = b16(20);
    uint16_t p25  = b16(22);
    uint16_t p50  = b16(24);
    uint16_t p100 = b16(26);

    readCount++;
    successCount++;

    // Status check
    const char* status = "OK";
    if (pm25_atm > 500) status = "VERY HIGH";
    else if (pm25_atm > 150) status = "HIGH";
    else if (pm25_atm > 55) status = "MODERATE";

    // Main reading line
    Serial.printf("  %-4lu   %-6u  %-6u  %-6u    %-6u  %-6u  %-6u    %s\n",
                  readCount, pm1_atm, pm25_atm, pm10_atm,
                  pm1_cf, pm25_cf, pm10_cf, status);

    // Particle counts (every 5th reading to reduce clutter)
    if (readCount % 5 == 0) {
        Serial.println("        ┌─ Particles per 0.1L ─────────────────────────────────────┐");
        Serial.printf( "        │  >0.3μm: %-5u  >0.5μm: %-5u  >1.0μm: %-5u              │\n",
                       p03, p05, p10);
        Serial.printf( "        │  >2.5μm: %-5u  >5.0μm: %-5u  >10μm:  %-5u              │\n",
                       p25, p50, p100);
        Serial.println("        └──────────────────────────────────────────────────────────┘");
    }
}

// ─── Setup ──────────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    delay(2000);  // Let serial terminal connect

    Serial.println("\n\n");
    Serial.println("################################################");
    Serial.println("#     PMS5003 SENSOR TEST — PP Monitoring      #");
    Serial.println("#                                               #");
    Serial.println("#  UART RX = GPIO5   (← PMS5003 TX)           #");
    Serial.println("#  UART TX = GPIO33  (→ PMS5003 RX)           #");
    Serial.println("#  Baud: 9600  Protocol: 8N1                   #");
    Serial.println("################################################\n");

    // Init Serial2 for PMS5003
    Serial2.begin(PMS_BAUD, SERIAL_8N1, PMS_RX_PIN, PMS_TX_PIN);
    Serial.printf("[PMS5003] Serial2 initialized — RX=GPIO%d  TX=GPIO%d  Baud=%d\n",
                  PMS_RX_PIN, PMS_TX_PIN, PMS_BAUD);

    // Warm-up period
    Serial.printf("[PMS5003] Warming up (%d seconds)...\n", PMS_WARMUP_MS / 1000);
    Serial.println("[PMS5003] The laser/fan needs time to stabilise.\n");

    // Show countdown
    for (int sec = PMS_WARMUP_MS / 1000; sec > 0; sec--) {
        Serial.printf("\r  Warm-up: %2d seconds remaining...  ", sec);
        delay(1000);

        // Check if we're already getting data during warmup
        if (sec % 10 == 0 && Serial2.available()) {
            Serial.printf("(bytes available: %d)", Serial2.available());
        }
    }

    // Flush any data that arrived during warmup
    while (Serial2.available()) Serial2.read();

    Serial.println("\n\n[PMS5003] Warm-up complete! Starting reads...\n");
    Serial.println("──────────────────────────────────────────────────────────────────────────");
    Serial.println("  #     PM1.0   PM2.5   PM10     PM1cf   PM25cf  PM10cf    Status");
    Serial.println("        (μg/m³ atmospheric)       (μg/m³ CF=1)");
    Serial.println("──────────────────────────────────────────────────────────────────────────");
}

// ─── Loop ───────────────────────────────────────────────────────────────────
void loop() {
    uint8_t buf[PMS_FRAME_LEN];

    // Flush stale data before reading
    while (Serial2.available()) Serial2.read();

    if (readPMSFrame(buf)) {
        displayFrame(buf);
    } else {
        readCount++;
        failCount++;
        Serial.printf("  %-4lu   --      --      --        --      --      --        READ FAILED\n",
                      readCount);

        // Show diagnostics on failure
        if (failCount >= 3 && failCount % 3 == 0) {
            Serial.println("\n  !! Multiple consecutive failures — check wiring:");
            Serial.println("  !!   PMS5003 TX  → GPIO5  (data from sensor)");
            Serial.println("  !!   PMS5003 RX  → GPIO33 (commands to sensor)");
            Serial.println("  !!   PMS5003 VCC → 5V");
            Serial.println("  !!   PMS5003 GND → GND");
            Serial.println("  !!   PMS5003 SET → 5V (or floating)\n");
            Serial.printf( "  Stats: %lu success / %lu fail / %lu total\n\n",
                           successCount, failCount, readCount);
        }
    }

    delay(2000);  // Read every 2 seconds
}
