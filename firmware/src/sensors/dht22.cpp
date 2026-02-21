/**
 * dht22.cpp
 * DHT22 Temperature & Humidity Sensor Driver — Implementation
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-22
 */

#include "dht22.h"

DHT22Sensor::DHT22Sensor(uint8_t pin)
    : _dht(pin, DHT_TYPE)
    , _pin(pin)
    , _lastReadOk(false)
    , _lastReadMs(0)
{}

void DHT22Sensor::begin() {
    _dht.begin();
    DEBUG_PRINTF("[DHT22] Initialized on GPIO%d\n", _pin);
    // DHT22 needs 1-2 seconds after power-on before first read
    delay(2000);
}

DHT22Reading DHT22Sensor::read() {
    DHT22Reading result = { NAN, NAN, false };

    for (uint8_t attempt = 1; attempt <= DHT_READ_RETRY; attempt++) {
        float temp = _dht.readTemperature();   // Celsius
        float hum  = _dht.readHumidity();

        if (_isValidReading(temp, hum)) {
            result.temperature = temp;
            result.humidity    = hum;
            result.valid       = true;
            _lastReadOk        = true;
            _lastReadMs        = millis();

            DEBUG_PRINTF("[DHT22] OK — Temp: %.1f°C  Humidity: %.1f%%\n", temp, hum);
            return result;
        }

        DEBUG_PRINTF("[DHT22] Read attempt %d/%d failed (temp=%.1f hum=%.1f)\n",
                     attempt, DHT_READ_RETRY, temp, hum);

        if (attempt < DHT_READ_RETRY) {
            delay(DHT_READ_DELAY_MS);
        }
    }

    _lastReadOk = false;
    DEBUG_PRINTLN("[DHT22] ERROR — All read attempts failed");
    return result;
}

bool DHT22Sensor::_isValidReading(float temp, float hum) const {
    // Reject NAN, infinity, and physically impossible values
    if (isnan(temp) || isnan(hum))     return false;
    if (isinf(temp) || isinf(hum))     return false;
    if (temp < -40.0f || temp > 80.0f) return false;  // DHT22 range: -40 to 80°C
    if (hum  < 0.0f   || hum  > 100.0f) return false; // 0–100% RH
    return true;
}
