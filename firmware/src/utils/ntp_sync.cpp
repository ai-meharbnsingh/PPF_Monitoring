/**
 * ntp_sync.cpp
 * NTP Time Sync Utility — Implementation
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-22
 */

#include "ntp_sync.h"

// ─── Constructor ──────────────────────────────────────────────────────────────
// NTPClient is constructed with UTC offset = 0 (we store UTC for the backend)
NTPSync::NTPSync()
    : _ntp(_udp, NTP_SERVER, 0, NTP_UPDATE_MS)
    , _synced(false)
    , _lastSyncMs(0)
{}


// ─── begin() ─────────────────────────────────────────────────────────────────
void NTPSync::begin() {
    _ntp.begin();
    DEBUG_PRINTF("[NTP] Server: %s  Offset: 0 (UTC)\n", NTP_SERVER);

    // Try to sync up to 5 times before giving up
    for (uint8_t i = 0; i < 5; i++) {
        if (_ntp.forceUpdate()) {
            _synced    = true;
            _lastSyncMs = millis();
            DEBUG_PRINTF("[NTP] Synced — UTC: %s  Epoch: %lu\n",
                         _ntp.getFormattedTime().c_str(),
                         (unsigned long)_ntp.getEpochTime());
            return;
        }
        DEBUG_PRINTF("[NTP] Sync attempt %d/5 failed\n", i + 1);
        delay(1000);
    }

    DEBUG_PRINTLN("[NTP] WARN — Initial sync failed. Timestamps will be unavailable "
                  "until network sync succeeds.");
}


// ─── update() ────────────────────────────────────────────────────────────────
void NTPSync::update() {
    // NTPClient::update() internally throttles using NTP_UPDATE_MS
    if (_ntp.update()) {
        if (!_synced) {
            DEBUG_PRINTF("[NTP] Synced (deferred) — UTC: %s\n",
                         _ntp.getFormattedTime().c_str());
        }
        _synced     = true;
        _lastSyncMs = millis();
    }
}


// ─── getTimestamp() ──────────────────────────────────────────────────────────
bool NTPSync::getTimestamp(char* buf, size_t len) const {
    if (!_synced || len < 21) return false;

    time_t epoch = (time_t)_ntp.getEpochTime();
    struct tm* t = gmtime(&epoch);

    // Format: "2026-02-22T10:30:00Z"
    snprintf(buf, len, "%04d-%02d-%02dT%02d:%02d:%02dZ",
             t->tm_year + 1900,
             t->tm_mon  + 1,
             t->tm_mday,
             t->tm_hour,
             t->tm_min,
             t->tm_sec);

    return true;
}


// ─── getEpoch() ──────────────────────────────────────────────────────────────
uint32_t NTPSync::getEpoch() const {
    if (!_synced) return 0;
    return _ntp.getEpochTime();
}
