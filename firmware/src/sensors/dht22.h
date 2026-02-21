/**
 * dht22.h
 * DHT22 Temperature & Humidity Sensor Driver
 *
 * Wraps the Adafruit DHT library with retry logic and error handling.
 * Returns NAN on read failure — caller must check with isnan().
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-22
 */

#pragma once

#include <Arduino.h>
#include <DHT.h>
#include "config.h"

struct DHT22Reading {
    float temperature;   // °C  — NAN if read failed
    float humidity;      // %   — NAN if read failed
    bool  valid;         // true only if both values are real numbers
};

class DHT22Sensor {
public:
    /**
     * @param pin   GPIO pin connected to DHT22 DATA line
     */
    explicit DHT22Sensor(uint8_t pin);

    /** Call once in setup(). */
    void begin();

    /**
     * Read sensor with up to DHT_READ_RETRY attempts.
     * Always returns a struct — check reading.valid before using values.
     */
    DHT22Reading read();

    /** True if the last read() call was successful. */
    bool isHealthy() const { return _lastReadOk; }

private:
    DHT      _dht;
    uint8_t  _pin;
    bool     _lastReadOk;
    uint32_t _lastReadMs;

    bool _isValidReading(float temp, float hum) const;
};
