/**
 * device_config.cpp
 * NVS-backed device configuration — Implementation
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-27
 */

#include "device_config.h"
#include <Preferences.h>
#include "config.h"

// NVS namespace and keys
static const char* NVS_NAMESPACE  = "ppf_config";
static const char* KEY_LICENSE    = "license_key";
static const char* KEY_WORKSHOP   = "workshop_id";
static const char* KEY_PIT        = "pit_id";

// Global singleton
DeviceConfig deviceConfig;

// Persistent Preferences handle
static Preferences _prefs;


void DeviceConfig::begin() {
    // Generate device ID and MAC from hardware
    _generateDeviceId();

    // Open NVS namespace (read-only first to load)
    _prefs.begin(NVS_NAMESPACE, true);  // true = read-only

    // Load license key
    String lic = _prefs.getString(KEY_LICENSE, "");
    if (lic.length() > 0 && lic.length() < sizeof(_licenseKey)) {
        strncpy(_licenseKey, lic.c_str(), sizeof(_licenseKey) - 1);
        _licenseKey[sizeof(_licenseKey) - 1] = '\0';
        _provisioned = true;
    } else {
        _licenseKey[0] = '\0';
        _provisioned = false;
    }

    // Load workshop and pit IDs
    _workshopId = _prefs.getInt(KEY_WORKSHOP, 0);
    _pitId      = _prefs.getInt(KEY_PIT, 0);

    _prefs.end();

    // Debug output
    DEBUG_PRINTLN("[CONFIG] NVS loaded:");
    DEBUG_PRINTF("[CONFIG]   Device ID:    %s\n", _deviceId);
    DEBUG_PRINTF("[CONFIG]   MAC:          %s\n", _macAddress);
    DEBUG_PRINTF("[CONFIG]   Provisioned:  %s\n", _provisioned ? "YES" : "NO");
    if (_provisioned) {
        DEBUG_PRINTF("[CONFIG]   License Key:  %s\n", _licenseKey);
        DEBUG_PRINTF("[CONFIG]   Workshop ID:  %d\n", _workshopId);
        DEBUG_PRINTF("[CONFIG]   Pit ID:       %d\n", _pitId);
    }
}


void DeviceConfig::saveLicenseKey(const char* key) {
    strncpy(_licenseKey, key, sizeof(_licenseKey) - 1);
    _licenseKey[sizeof(_licenseKey) - 1] = '\0';
    _provisioned = true;

    _prefs.begin(NVS_NAMESPACE, false);  // false = read-write
    _prefs.putString(KEY_LICENSE, key);
    _prefs.end();

    DEBUG_PRINTF("[CONFIG] Saved license key: %s\n", key);
}


void DeviceConfig::saveWorkshopId(int id) {
    _workshopId = id;

    _prefs.begin(NVS_NAMESPACE, false);
    _prefs.putInt(KEY_WORKSHOP, id);
    _prefs.end();

    DEBUG_PRINTF("[CONFIG] Saved workshop ID: %d\n", id);
}


void DeviceConfig::savePitId(int id) {
    _pitId = id;

    _prefs.begin(NVS_NAMESPACE, false);
    _prefs.putInt(KEY_PIT, id);
    _prefs.end();

    DEBUG_PRINTF("[CONFIG] Saved pit ID: %d\n", id);
}


void DeviceConfig::clearAll() {
    _prefs.begin(NVS_NAMESPACE, false);
    _prefs.clear();
    _prefs.end();

    _licenseKey[0] = '\0';
    _workshopId = 0;
    _pitId = 0;
    _provisioned = false;

    DEBUG_PRINTLN("[CONFIG] All NVS config cleared (factory reset)");
}


void DeviceConfig::_generateDeviceId() {
    // Read the burnt-in MAC from eFuse
    uint8_t mac[6];
    esp_efuse_mac_get_default(mac);

    // Build DEVICE_ID: "ESP32-" + 12 hex chars (uppercase, no colons)
    // Same format as the previously hardcoded value: "ESP32-083AF2A9F084"
    snprintf(_deviceId, sizeof(_deviceId),
             "ESP32-%02X%02X%02X%02X%02X%02X",
             mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);

    // Build human-readable MAC: "08:3A:F2:A9:F0:84"
    snprintf(_macAddress, sizeof(_macAddress),
             "%02X:%02X:%02X:%02X:%02X:%02X",
             mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
}
