/**
 * device_config.h
 * NVS-backed device configuration for zero-config provisioning.
 *
 * Stores license_key, workshop_id, and pit_id in ESP32 NVS flash.
 * Auto-generates DEVICE_ID from the chip's burnt-in MAC address.
 * NVS data survives OTA firmware updates (only app partition is overwritten).
 *
 * Usage:
 *   deviceConfig.begin();
 *   if (!deviceConfig.isProvisioned()) { ... provisioning mode ... }
 *   else { ... normal mode using getDeviceId(), getLicenseKey(), etc. ... }
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-27
 */

#pragma once

#include <Arduino.h>

class DeviceConfig {
public:
    /**
     * Initialize NVS and load stored config.
     * Also generates DEVICE_ID from MAC address.
     * Call once in setup() before checking isProvisioned().
     */
    void begin();

    /** @return true if a license_key is stored in NVS (device has been approved) */
    bool isProvisioned() const { return _provisioned; }

    // ── Getters (cached in RAM after begin()) ─────────────────────────────
    const char* getDeviceId() const   { return _deviceId; }
    const char* getLicenseKey() const  { return _licenseKey; }
    const char* getMacAddress() const  { return _macAddress; }
    int  getWorkshopId() const         { return _workshopId; }
    int  getPitId() const              { return _pitId; }

    // ── Setters (write to NVS immediately) ────────────────────────────────
    void saveLicenseKey(const char* key);
    void saveWorkshopId(int id);
    void savePitId(int id);

    /** Erase all stored config (factory reset). Call clearAll() then ESP.restart(). */
    void clearAll();

private:
    char _deviceId[24];     // "ESP32-" + 12 hex chars + null
    char _licenseKey[20];   // "LIC-XXXX-XXXX-XXXX" + null
    char _macAddress[18];   // "08:3A:F2:A9:F0:84" + null
    int  _workshopId = 0;
    int  _pitId = 0;
    bool _provisioned = false;

    /** Generate DEVICE_ID and MAC string from ESP32 eFuse MAC */
    void _generateDeviceId();
};

// Global singleton — include this header and use directly
extern DeviceConfig deviceConfig;
