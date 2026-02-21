/**
 * pms5003.h
 * PMS5003 Particulate Matter Sensor Driver — Header
 *
 * Parses the 32-byte UART data frame from the Plantower PMS5003.
 *
 * Wiring (Olimex ESP32-GATEWAY):
 *   PMS5003 TX → ESP32 GPIO32  (Serial2 RX)
 *   PMS5003 RX → ESP32 GPIO33  (Serial2 TX)
 *   PMS5003 VCC → 5V
 *   PMS5003 GND → GND
 *
 * Frame structure (32 bytes):
 *   [0] 0x42  [1] 0x4D  — start bytes
 *   [2-3]   frame length (28)
 *   [4-5]   PM1.0  CF=1  μg/m³
 *   [6-7]   PM2.5  CF=1  μg/m³
 *   [8-9]   PM10   CF=1  μg/m³
 *   [10-11] PM1.0  atmospheric  μg/m³
 *   [12-13] PM2.5  atmospheric  μg/m³
 *   [14-15] PM10   atmospheric  μg/m³
 *   [16-17] particles > 0.3 μm / 0.1 L
 *   [18-19] particles > 0.5 μm / 0.1 L
 *   [20-21] particles > 1.0 μm / 0.1 L
 *   [22-23] particles > 2.5 μm / 0.1 L
 *   [24-25] particles > 5.0 μm / 0.1 L
 *   [26-27] particles > 10  μm / 0.1 L
 *   [28-29] reserved
 *   [30-31] checksum (sum of all previous bytes)
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-22
 */

#pragma once

#include <Arduino.h>
#include "config.h"

// ─── Frame constants ──────────────────────────────────────────────────────────
static constexpr uint8_t  PMS_FRAME_LEN    = 32;
static constexpr uint8_t  PMS_START_BYTE_1 = 0x42;
static constexpr uint8_t  PMS_START_BYTE_2 = 0x4D;


// ─── Reading struct ───────────────────────────────────────────────────────────
struct PMS5003Reading {
    // Atmospheric concentration μg/m³ (use these for air quality reporting)
    uint16_t pm1;       // PM1.0
    uint16_t pm25;      // PM2.5
    uint16_t pm10;      // PM10

    // Particle counts per 0.1 L (used for detailed logging / backend)
    uint16_t particles_03um;
    uint16_t particles_05um;
    uint16_t particles_10um;
    uint16_t particles_25um;
    uint16_t particles_50um;
    uint16_t particles_100um;

    bool valid;
};


// ─── Driver class ─────────────────────────────────────────────────────────────
class PMS5003Sensor {
public:
    /**
     * @param rxPin  ESP32 pin connected to PMS5003 TX
     * @param txPin  ESP32 pin connected to PMS5003 RX
     */
    PMS5003Sensor(uint8_t rxPin, uint8_t txPin);

    /**
     * Initialises Serial2, waits for warmup.
     * Call once from setup().
     */
    void begin();

    /**
     * Attempts to read one valid frame.
     * Blocks for up to PMS5003_TIMEOUT_MS waiting for the frame.
     * @return  PMS5003Reading — check .valid before using data
     */
    PMS5003Reading read();

    /** @return true if the last call to read() succeeded */
    bool isHealthy() const { return _lastReadOk; }

private:
    uint8_t  _rxPin;
    uint8_t  _txPin;
    bool     _lastReadOk;

    /** Parse a 32-byte buffer that is already aligned to the start bytes.
     *  Returns false if checksum fails. */
    bool _parseFrame(const uint8_t* buf, PMS5003Reading& out) const;

    /** Read exactly one 32-byte frame from Serial2.
     *  Returns false on timeout or checksum error. */
    bool _readFrame(PMS5003Reading& out);

    /** Consume and discard incoming bytes until start sequence is found,
     *  then read the remaining bytes of the frame.
     *  Returns false on timeout. */
    bool _syncAndRead(uint8_t* buf);
};
