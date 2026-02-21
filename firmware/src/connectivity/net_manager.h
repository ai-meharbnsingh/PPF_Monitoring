/**
 * net_manager.h
 * Network Manager — Header
 *
 * Handles both Ethernet (Olimex ESP32-GATEWAY LAN8720A) and WiFi connections.
 * Selected at compile time via platformio.ini build flags:
 *   -D USE_ETHERNET  → Ethernet (default for ESP32-GATEWAY)
 *   (no flag)        → WiFi
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-22
 */

#pragma once

#include <Arduino.h>
#include "config.h"

#ifdef USE_ETHERNET
  #include <ETH.h>
#else
  #include <WiFi.h>
#endif


// ─── Network Manager ─────────────────────────────────────────────────────────
class NetManager {
public:
    NetManager() = default;

    /**
     * Initialise the network interface and wait for connection.
     * For Ethernet: ETH.begin() with Olimex ESP32-GATEWAY pin mapping.
     * For WiFi:     WiFi.begin() with SSID/password from config.h.
     *
     * Blocks until connected or timeout. If timeout, device continues
     * and will retry in ensureConnected().
     */
    void begin();

    /**
     * Check connectivity; attempt to reconnect if disconnected.
     * Call this at the start of every loop() iteration.
     * @return true if network is up
     */
    bool ensureConnected();

    /** @return true if network interface reports link/connection is up */
    bool isConnected() const;

    /** @return IP address as string, or "0.0.0.0" if not connected */
    String getIPAddress() const;

    /** @return interface type string: "Ethernet" or "WiFi" */
    static const char* interfaceType();

private:
    bool _everConnected = false;

#ifdef USE_ETHERNET
    void _initEthernet();
    static void _ethEventHandler(WiFiEvent_t event);
    static volatile bool _ethLinkUp;
    static volatile bool _ethGotIP;
#else
    void _initWiFi();
    uint32_t _lastReconnectAttemptMs = 0;
#endif
};
