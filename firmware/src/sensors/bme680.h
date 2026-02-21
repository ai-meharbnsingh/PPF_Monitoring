/**
 * bme680.h
 * BME680 Environmental Sensor Driver — Header
 *
 * Wraps the Adafruit BME680 library.
 * Used ONLY when SENSOR_CONFIG_BME680 is defined in config.h.
 *
 * Wiring (Olimex ESP32-GATEWAY — Ethernet mode):
 *   BME680 SDA → GPIO13
 *   BME680 SCL → GPIO14
 *   BME680 VCC → 3.3V
 *   BME680 GND → GND
 *   BME680 SDO → GND   (I2C address = 0x76)  OR
 *   BME680 SDO → 3.3V  (I2C address = 0x77) ← default in config.h
 *
 * Wiring (WiFi mode — standard I2C):
 *   BME680 SDA → GPIO21
 *   BME680 SCL → GPIO22
 *
 * Note: BSEC (Bosch Sensor Environmental Cluster) for proper IAQ is not
 *       included here as it requires a closed-source library blob.
 *       IAQ is estimated via gas resistance ratio as a simplified proxy.
 *       For full BSEC integration, replace _computeIaq() with BSEC calls.
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-22
 */

#pragma once

#ifdef SENSOR_CONFIG_BME680

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_BME680.h>
#include "config.h"


// ─── Reading struct ───────────────────────────────────────────────────────────
struct BME680Reading {
    float    temperature;    // °C  (with BME680_TEMP_OFFSET applied)
    float    humidity;       // %RH
    float    pressure;       // hPa
    float    gas_resistance; // Ω  (raw MOX sensor resistance)
    float    iaq;            // 0–500 IAQ index (simplified estimate)
    uint8_t  iaq_accuracy;   // 0–3  (always 1 for simplified calc; 3 for BSEC)
    bool     valid;
};


// ─── Driver class ─────────────────────────────────────────────────────────────
class BME680Sensor {
public:
    /**
     * @param sdaPin  I2C SDA — GPIO13 for Ethernet, GPIO21 for WiFi
     * @param sclPin  I2C SCL — GPIO14 for Ethernet, GPIO22 for WiFi
     * @param i2cAddr I2C address — BME680_I2C_ADDR (0x77 by default)
     */
    BME680Sensor(uint8_t sdaPin, uint8_t sclPin,
                 uint8_t i2cAddr = BME680_I2C_ADDR);

    /**
     * Initialise I2C and BME680.
     * Call once from setup().
     * Returns false if sensor not found.
     */
    bool begin();

    /**
     * Trigger a measurement and return results.
     * Blocks for up to ~200 ms while sensor performs measurement.
     * @return BME680Reading — check .valid before use
     */
    BME680Reading read();

    /** @return true if the last read() call succeeded */
    bool isHealthy() const { return _lastReadOk; }

private:
    uint8_t           _sdaPin;
    uint8_t           _sclPin;
    uint8_t           _i2cAddr;
    bool              _lastReadOk;
    bool              _initialized;
    Adafruit_BME680   _bme;

    // Baseline gas resistance for IAQ calculation (updated over time)
    float             _gasBaseline;
    bool              _gasBaselineSet;

    /**
     * Simplified IAQ estimate from gas resistance.
     * Range 0–500; lower is better air quality.
     * Not a substitute for Bosch BSEC calibrated IAQ.
     */
    float _computeIaq(float gasResistance, float humidity);

    /** Validate reading ranges. */
    bool _isValid(const BME680Reading& r) const;
};

#endif // SENSOR_CONFIG_BME680
