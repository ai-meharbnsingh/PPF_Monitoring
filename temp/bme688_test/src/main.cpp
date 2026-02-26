/**
 * BME688 Sensor Test
 *
 * Standalone sketch to verify BME688 (or BME680) is wired correctly
 * and returning valid data on the I2C bus.
 *
 * Wiring (WiFi mode — standard I2C):
 *   BME688 SDA → GPIO21
 *   BME688 SCL → GPIO22
 *   BME688 VCC → 3.3V
 *   BME688 GND → GND
 *
 * I2C Address:
 *   0x77 (default, SDO floating or HIGH)
 *   0x76 (SDO tied to GND)
 *
 * This sketch auto-scans both addresses.
 */

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_BME680.h>

// ─── Pin definitions (WiFi mode) ────────────────────────────────────────────
#define I2C_SDA  21
#define I2C_SCL  22

// ─── Globals ────────────────────────────────────────────────────────────────
Adafruit_BME680 bme;
uint8_t sensorAddr = 0;
bool sensorFound   = false;
unsigned long readCount = 0;

// ─── I2C Scanner ────────────────────────────────────────────────────────────
void scanI2C() {
    Serial.println("\n========================================");
    Serial.println("  I2C BUS SCAN  (SDA=21, SCL=22)");
    Serial.println("========================================");

    int devicesFound = 0;
    for (uint8_t addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        uint8_t err = Wire.endTransmission();
        if (err == 0) {
            Serial.printf("  Found device at 0x%02X", addr);
            if (addr == 0x76 || addr == 0x77) {
                Serial.print("  <-- BME680/BME688");
            }
            Serial.println();
            devicesFound++;
        }
    }

    if (devicesFound == 0) {
        Serial.println("  ** NO I2C DEVICES FOUND **");
        Serial.println("  Check wiring:");
        Serial.println("    SDA -> GPIO21");
        Serial.println("    SCL -> GPIO22");
        Serial.println("    VCC -> 3.3V");
        Serial.println("    GND -> GND");
    } else {
        Serial.printf("  Total: %d device(s) found\n", devicesFound);
    }
    Serial.println("========================================\n");
}

// ─── Try to init BME688 at given address ────────────────────────────────────
bool tryInit(uint8_t addr) {
    Serial.printf("[BME688] Trying address 0x%02X ... ", addr);
    if (bme.begin(addr, &Wire)) {
        Serial.println("SUCCESS!");
        return true;
    }
    Serial.println("not found");
    return false;
}

// ─── Setup ──────────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    delay(2000);  // Let serial terminal connect

    Serial.println("\n\n");
    Serial.println("################################################");
    Serial.println("#       BME688 SENSOR TEST — PP Monitoring     #");
    Serial.println("#                                               #");
    Serial.println("#  I2C SDA = GPIO21    I2C SCL = GPIO22        #");
    Serial.println("#  Baud: 115200                                 #");
    Serial.println("################################################\n");

    // Init I2C
    Wire.begin(I2C_SDA, I2C_SCL);
    delay(100);

    // Scan the bus first
    scanI2C();

    // Try both addresses
    if (tryInit(0x77)) {
        sensorAddr = 0x77;
        sensorFound = true;
    } else if (tryInit(0x76)) {
        sensorAddr = 0x76;
        sensorFound = true;
    }

    if (!sensorFound) {
        Serial.println("\n!! BME688 NOT FOUND on 0x76 or 0x77 !!");
        Serial.println("!! Check wiring and try again.        !!\n");
        Serial.println("Will keep scanning every 5 seconds...\n");
        return;
    }

    // Configure sensor (Bosch recommended for IAQ)
    bme.setTemperatureOversampling(BME680_OS_8X);
    bme.setHumidityOversampling(BME680_OS_2X);
    bme.setPressureOversampling(BME680_OS_4X);
    bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
    bme.setGasHeater(320, 150);  // 320C for 150ms — standard MOX activation

    Serial.printf("\n[BME688] Initialized at 0x%02X\n", sensorAddr);
    Serial.println("[BME688] Config: TempOS=8x  HumOS=2x  PresOS=4x  IIR=3  Gas=320C/150ms");
    Serial.println("[BME688] First reading may be inaccurate (warm-up)...\n");

    // Discard first reading (unreliable)
    bme.performReading();
    delay(500);

    Serial.println("─────────────────────────────────────────────────────────────────────");
    Serial.println("  #    Temp(C)   Hum(%)   Press(hPa)   Gas(kOhm)   Status");
    Serial.println("─────────────────────────────────────────────────────────────────────");
}

// ─── Loop ───────────────────────────────────────────────────────────────────
void loop() {
    if (!sensorFound) {
        // Keep trying to find sensor
        Serial.println("[RETRY] Scanning I2C bus...");
        Wire.begin(I2C_SDA, I2C_SCL);
        delay(100);
        scanI2C();

        if (tryInit(0x77)) {
            sensorAddr = 0x77;
            sensorFound = true;
        } else if (tryInit(0x76)) {
            sensorAddr = 0x76;
            sensorFound = true;
        }

        if (sensorFound) {
            bme.setTemperatureOversampling(BME680_OS_8X);
            bme.setHumidityOversampling(BME680_OS_2X);
            bme.setPressureOversampling(BME680_OS_4X);
            bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
            bme.setGasHeater(320, 150);
            bme.performReading();
            delay(500);
            Serial.println("\n─────────────────────────────────────────────────────────────────────");
            Serial.println("  #    Temp(C)   Hum(%)   Press(hPa)   Gas(kOhm)   Status");
            Serial.println("─────────────────────────────────────────────────────────────────────");
        } else {
            delay(5000);
            return;
        }
    }

    // Read sensor
    if (!bme.performReading()) {
        Serial.printf("  %-4lu   --        --        --           --         READ FAILED\n",
                       ++readCount);
        delay(3000);
        return;
    }

    float temp     = bme.temperature;
    float hum      = bme.humidity;
    float press    = bme.pressure / 100.0f;  // Pa -> hPa
    float gasKOhm  = bme.gas_resistance / 1000.0f;  // Ohm -> kOhm

    readCount++;

    // Status check
    const char* status = "OK";
    if (isnan(temp) || temp < -40 || temp > 85)      status = "TEMP ERR";
    else if (isnan(hum) || hum < 0 || hum > 100)     status = "HUM ERR";
    else if (isnan(press) || press < 300 || press > 1100) status = "PRESS ERR";
    else if (gasKOhm < 0.1)                          status = "GAS LOW";

    Serial.printf("  %-4lu   %6.2f    %5.2f    %7.2f      %7.2f     %s\n",
                   readCount, temp, hum, press, gasKOhm, status);

    delay(3000);  // Read every 3 seconds
}
