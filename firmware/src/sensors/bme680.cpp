/**
 * bme680.cpp
 * BME680 Environmental Sensor Driver — Implementation
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-22
 */

#include "config.h"

#if defined(SENSOR_CONFIG_BME680) || defined(SENSOR_CONFIG_BME688_DHT_FALLBACK)

#include "bme680.h"

// ─────────────────────────────────────────────────────────────────────────────
// IAQ estimation constants
// Derived from Bosch application notes (simplified, no BSEC)
// ─────────────────────────────────────────────────────────────────────────────
static constexpr float IAQ_HUM_WEIGHT    = 0.25f;  // humidity contribution
static constexpr float IAQ_GAS_WEIGHT    = 0.75f;  // gas resistance contribution
static constexpr float IAQ_IDEAL_HUM     = 40.0f;  // % RH considered optimal
static constexpr float IAQ_GAS_FLOOR     = 5000.0f; // Ω — treated as worst case


// ─── Constructor ──────────────────────────────────────────────────────────────
BME680Sensor::BME680Sensor(uint8_t sdaPin, uint8_t sclPin, uint8_t i2cAddr)
    : _sdaPin(sdaPin)
    , _sclPin(sclPin)
    , _i2cAddr(i2cAddr)
    , _lastReadOk(false)
    , _initialized(false)
    , _gasBaseline(0.0f)
    , _gasBaselineSet(false)
{}


// ─── begin() ─────────────────────────────────────────────────────────────────
bool BME680Sensor::begin() {
    Wire.begin(_sdaPin, _sclPin);
    DEBUG_PRINTF("[BME680] I2C on SDA=GPIO%d  SCL=GPIO%d  Addr=0x%02X\n",
                 _sdaPin, _sclPin, _i2cAddr);

    if (!_bme.begin(_i2cAddr, &Wire)) {
        DEBUG_PRINTLN("[BME680] ERROR — Sensor not found. Check wiring/address.");
        return false;
    }

    // ── Sensor settings ────────────────────────────────────────────────────
    // These match Bosch recommended settings for typical IAQ use
    _bme.setTemperatureOversampling(BME680_OS_8X);
    _bme.setHumidityOversampling(BME680_OS_2X);
    _bme.setPressureOversampling(BME680_OS_4X);
    _bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
    _bme.setGasHeater(320, 150);   // 320°C for 150 ms — standard MOX activation

    _initialized = true;
    DEBUG_PRINTLN("[BME680] Initialized OK");

    // First reading is unreliable — trigger and discard
    _bme.performReading();
    delay(200);

    return true;
}


// ─── read() ──────────────────────────────────────────────────────────────────
BME680Reading BME680Sensor::read() {
    BME680Reading result = {};
    result.valid = false;

    if (!_initialized) {
        DEBUG_PRINTLN("[BME680] ERROR — Not initialized. Call begin() first.");
        return result;
    }

    for (uint8_t attempt = 1; attempt <= DHT_READ_RETRY; attempt++) {
        if (!_bme.performReading()) {
            DEBUG_PRINTF("[BME680] Read attempt %d/%d failed — performReading() error\n",
                         attempt, DHT_READ_RETRY);
            if (attempt < DHT_READ_RETRY) delay(DHT_READ_DELAY_MS);
            continue;
        }

        result.temperature    = _bme.temperature + BME680_TEMP_OFFSET;
        result.humidity       = _bme.humidity;
        result.pressure       = _bme.pressure / 100.0f;   // Pa → hPa
        result.gas_resistance = (float)_bme.gas_resistance;
        result.iaq            = _computeIaq(result.gas_resistance, result.humidity);
        result.iaq_accuracy   = 1;   // simplified calc — accuracy level 1

        if (_isValid(result)) {
            result.valid  = true;
            _lastReadOk   = true;

            DEBUG_PRINTF("[BME680] OK — Temp=%.1f°C  Hum=%.1f%%  Press=%.1fhPa  "
                         "Gas=%.0fΩ  IAQ=%.1f\n",
                         result.temperature, result.humidity, result.pressure,
                         result.gas_resistance, result.iaq);
            return result;
        }

        DEBUG_PRINTF("[BME680] Attempt %d/%d invalid reading\n", attempt, DHT_READ_RETRY);
        if (attempt < DHT_READ_RETRY) delay(DHT_READ_DELAY_MS);
    }

    _lastReadOk = false;
    DEBUG_PRINTLN("[BME680] ERROR — All read attempts failed");
    return result;
}


// ─── _computeIaq() ───────────────────────────────────────────────────────────
float BME680Sensor::_computeIaq(float gasResistance, float humidity) {
    // Update baseline with exponential moving average
    if (!_gasBaselineSet || gasResistance > _gasBaseline) {
        _gasBaseline    = gasResistance;
        _gasBaselineSet = true;
    } else {
        // Slowly drift baseline upward (0.5% per reading)
        _gasBaseline = _gasBaseline * 0.995f + gasResistance * 0.005f;
    }

    // Gas score: 0.0 (worst) → 1.0 (best)
    // Avoid divide-by-zero if baseline is very low
    float gasRef  = max(_gasBaseline, IAQ_GAS_FLOOR);
    float gasNorm = constrain(gasResistance / gasRef, 0.0f, 1.0f);
    float gasScore = gasNorm * IAQ_GAS_WEIGHT;

    // Humidity score: 0.0 (worst) → IAQ_HUM_WEIGHT (best) at ideal humidity
    float humDev   = fabsf(humidity - IAQ_IDEAL_HUM);
    float humScore = IAQ_HUM_WEIGHT * (1.0f - constrain(humDev / IAQ_IDEAL_HUM, 0.0f, 1.0f));

    // Combined score 0.0–1.0, then map to IAQ 0–500 (lower = better)
    float combined = gasScore + humScore;
    float iaq      = 500.0f * (1.0f - constrain(combined, 0.0f, 1.0f));

    return iaq;
}


// ─── _isValid() ──────────────────────────────────────────────────────────────
bool BME680Sensor::_isValid(const BME680Reading& r) const {
    if (isnan(r.temperature) || r.temperature < -40.0f || r.temperature > 85.0f) return false;
    if (isnan(r.humidity)    || r.humidity    < 0.0f   || r.humidity    > 100.0f) return false;
    if (isnan(r.pressure)    || r.pressure    < 300.0f || r.pressure    > 1100.0f) return false;
    if (isnan(r.gas_resistance) || r.gas_resistance < 0.0f) return false;
    return true;
}

#endif // SENSOR_CONFIG_BME680 || SENSOR_CONFIG_BME688_DHT_FALLBACK
