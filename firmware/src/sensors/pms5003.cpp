/**
 * pms5003.cpp
 * PMS5003 Particulate Matter Sensor Driver — Implementation
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-22
 */

#include "pms5003.h"

// Serial2 is the hardware UART we use for the PMS5003
#define PMS_SERIAL Serial2


// ─── Constructor ──────────────────────────────────────────────────────────────
PMS5003Sensor::PMS5003Sensor(uint8_t rxPin, uint8_t txPin)
    : _rxPin(rxPin)
    , _txPin(txPin)
    , _lastReadOk(false)
{}


// ─── begin() ─────────────────────────────────────────────────────────────────
void PMS5003Sensor::begin() {
    PMS_SERIAL.begin(PMS5003_BAUD, SERIAL_8N1, _rxPin, _txPin);
    DEBUG_PRINTF("[PMS5003] Initialized — RX=GPIO%d  TX=GPIO%d  Baud=%d\n",
                 _rxPin, _txPin, PMS5003_BAUD);

    // PMS5003 needs ~30 s after power-on for the laser fan to stabilise
    DEBUG_PRINTF("[PMS5003] Warming up (%d ms)…\n", PMS5003_WARMUP_MS);
    delay(PMS5003_WARMUP_MS);
    DEBUG_PRINTLN("[PMS5003] Warm-up complete");
}


// ─── read() ──────────────────────────────────────────────────────────────────
PMS5003Reading PMS5003Sensor::read() {
    PMS5003Reading result = {};
    result.valid = false;

    for (uint8_t attempt = 1; attempt <= DHT_READ_RETRY; attempt++) {
        // Flush any stale data before reading a fresh frame
        while (PMS_SERIAL.available()) PMS_SERIAL.read();

        if (_readFrame(result)) {
            _lastReadOk = true;
            DEBUG_PRINTF("[PMS5003] OK — PM1=%-4u  PM2.5=%-4u  PM10=%-4u μg/m³\n",
                         result.pm1, result.pm25, result.pm10);
            return result;
        }

        DEBUG_PRINTF("[PMS5003] Read attempt %d/%d failed\n", attempt, DHT_READ_RETRY);
        if (attempt < DHT_READ_RETRY) delay(DHT_READ_DELAY_MS);
    }

    _lastReadOk = false;
    DEBUG_PRINTLN("[PMS5003] ERROR — All read attempts failed");
    return result;
}


// ─── _readFrame() ────────────────────────────────────────────────────────────
bool PMS5003Sensor::_readFrame(PMS5003Reading& out) {
    uint8_t buf[PMS_FRAME_LEN];

    if (!_syncAndRead(buf)) return false;
    return _parseFrame(buf, out);
}


// ─── _syncAndRead() ──────────────────────────────────────────────────────────
bool PMS5003Sensor::_syncAndRead(uint8_t* buf) {
    uint32_t deadline = millis() + PMS5003_TIMEOUT_MS;

    // Search for start bytes 0x42 0x4D
    uint8_t prev = 0;
    while (millis() < deadline) {
        if (!PMS_SERIAL.available()) {
            delay(1);
            continue;
        }
        uint8_t b = (uint8_t)PMS_SERIAL.read();
        if (prev == PMS_START_BYTE_1 && b == PMS_START_BYTE_2) {
            buf[0] = PMS_START_BYTE_1;
            buf[1] = PMS_START_BYTE_2;
            break;
        }
        prev = b;
    }

    if (millis() >= deadline) {
        DEBUG_PRINTLN("[PMS5003] Timeout waiting for start bytes");
        return false;
    }

    // Read the remaining 30 bytes
    uint8_t idx = 2;
    while (idx < PMS_FRAME_LEN && millis() < deadline) {
        if (PMS_SERIAL.available()) {
            buf[idx++] = (uint8_t)PMS_SERIAL.read();
        } else {
            delay(1);
        }
    }

    if (idx < PMS_FRAME_LEN) {
        DEBUG_PRINTLN("[PMS5003] Timeout reading frame body");
        return false;
    }

    return true;
}


// ─── _parseFrame() ───────────────────────────────────────────────────────────
bool PMS5003Sensor::_parseFrame(const uint8_t* buf, PMS5003Reading& out) const {
    // Verify start bytes (defensive — _syncAndRead already ensured this)
    if (buf[0] != PMS_START_BYTE_1 || buf[1] != PMS_START_BYTE_2) {
        DEBUG_PRINTLN("[PMS5003] Bad start bytes");
        return false;
    }

    // Checksum: sum of bytes [0..29] must equal the uint16 at [30..31]
    uint16_t calcSum = 0;
    for (uint8_t i = 0; i < 30; i++) calcSum += buf[i];
    uint16_t frameSum = ((uint16_t)buf[30] << 8) | buf[31];

    if (calcSum != frameSum) {
        DEBUG_PRINTF("[PMS5003] Checksum mismatch: calc=0x%04X frame=0x%04X\n",
                     calcSum, frameSum);
        return false;
    }

    // Helper lambda — combine two consecutive bytes into a uint16.
    // Named 'b16' (not 'word') to avoid collision with Arduino's
    // #define word(...) makeWord(...) macro which is not linked on ESP32.
    auto b16 = [&](uint8_t i) -> uint16_t {
        return ((uint16_t)buf[i] << 8) | buf[i + 1];
    };

    // Atmospheric concentration values (bytes 10–15)
    out.pm1  = b16(10);
    out.pm25 = b16(12);
    out.pm10 = b16(14);

    // Particle counts per 0.1 L (bytes 16–27)
    out.particles_03um  = b16(16);
    out.particles_05um  = b16(18);
    out.particles_10um  = b16(20);
    out.particles_25um  = b16(22);
    out.particles_50um  = b16(24);
    out.particles_100um = b16(26);

    out.valid = true;
    return true;
}
