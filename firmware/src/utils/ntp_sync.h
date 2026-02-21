/**
 * ntp_sync.h
 * NTP Time Sync Utility — Header
 *
 * Wraps NTPClient to keep the ESP32 clock synchronised.
 * Generates ISO 8601 UTC timestamps required by the backend.
 *
 * Backend expects: "2026-02-21T10:30:00Z"
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-22
 */

#pragma once

#include <Arduino.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include "config.h"


// ─── NTP Sync ─────────────────────────────────────────────────────────────────
class NTPSync {
public:
    NTPSync();

    /**
     * Initialise NTPClient and perform first sync.
     * Should be called once the network is up.
     */
    void begin();

    /**
     * Re-sync if NTP_UPDATE_MS has elapsed since last sync.
     * Call once per loop() iteration.
     */
    void update();

    /**
     * Get ISO 8601 UTC timestamp string.
     * Format: "2026-02-22T10:30:00Z"
     *
     * @param buf   Output buffer
     * @param len   Buffer size (must be >= 21 bytes)
     * @return true if time is valid and string was written
     */
    bool getTimestamp(char* buf, size_t len) const;

    /** @return true if NTP has successfully synced at least once */
    bool isSynced() const { return _synced; }

    /** @return Unix epoch time, or 0 if not synced */
    uint32_t getEpoch() const;

private:
    WiFiUDP     _udp;
    NTPClient   _ntp;
    bool        _synced;
    uint32_t    _lastSyncMs;
};
