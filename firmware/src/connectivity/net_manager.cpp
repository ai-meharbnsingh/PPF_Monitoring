/**
 * net_manager.cpp
 * Network Manager — Implementation
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-22
 */

#include "net_manager.h"

// ─────────────────────────────────────────────────────────────────────────────
// Olimex ESP32-GATEWAY LAN8720A pin mapping
// These MUST match the board schematic — do not change without hardware review.
// ─────────────────────────────────────────────────────────────────────────────
#ifdef USE_ETHERNET

// ETH.h (both Arduino-ESP32 1.x and 2.x) defines these as #define macros with
// default values. Undefine them first so we can declare typed constexpr
// variables with the board-specific values for the Olimex ESP32-GATEWAY
// (LAN8720A, clock on GPIO17).
#undef ETH_PHY_ADDR
#undef ETH_PHY_POWER
#undef ETH_PHY_MDC
#undef ETH_PHY_MDIO
#undef ETH_CLK_MODE
#undef ETH_PHY_TYPE

static constexpr int ETH_PHY_ADDR = 0;
static constexpr int ETH_PHY_POWER = -1; // no power pin on this board
static constexpr int ETH_PHY_MDC = 23;
static constexpr int ETH_PHY_MDIO = 18;
static constexpr eth_clock_mode_t ETH_CLK_MODE = ETH_CLOCK_GPIO17_OUT;
static constexpr eth_phy_type_t ETH_PHY_TYPE = ETH_PHY_LAN8720;

// Arduino-ESP32 1.x uses SYSTEM_EVENT_ETH_*, 2.x uses ARDUINO_EVENT_ETH_*.
// Provide backward-compat aliases when building against the old 1.x framework.
#ifndef ARDUINO_EVENT_ETH_START
#define ARDUINO_EVENT_ETH_START SYSTEM_EVENT_ETH_START
#define ARDUINO_EVENT_ETH_CONNECTED SYSTEM_EVENT_ETH_CONNECTED
#define ARDUINO_EVENT_ETH_GOT_IP SYSTEM_EVENT_ETH_GOT_IP
#define ARDUINO_EVENT_ETH_DISCONNECTED SYSTEM_EVENT_ETH_DISCONNECTED
#define ARDUINO_EVENT_ETH_STOP SYSTEM_EVENT_ETH_STOP
#endif

volatile bool NetManager::_ethLinkUp = false;
volatile bool NetManager::_ethGotIP = false;

// ── Ethernet event handler ───────────────────────────────────────────────────
void NetManager::_ethEventHandler(WiFiEvent_t event) {
  switch (event) {
  case ARDUINO_EVENT_ETH_START:
    DEBUG_PRINTLN("[NET] Ethernet started");
    ETH.setHostname("ppf-monitor");
    break;
  case ARDUINO_EVENT_ETH_CONNECTED:
    DEBUG_PRINTLN("[NET] Ethernet cable connected");
    _ethLinkUp = true;
    break;
  case ARDUINO_EVENT_ETH_GOT_IP:
    DEBUG_PRINTF("[NET] Ethernet IP: %s  Speed: %d Mbps  %s-duplex\n",
                 ETH.localIP().toString().c_str(), ETH.linkSpeed(),
                 ETH.fullDuplex() ? "full" : "half");
    _ethGotIP = true;
    break;
  case ARDUINO_EVENT_ETH_DISCONNECTED:
    DEBUG_PRINTLN("[NET] Ethernet disconnected");
    _ethLinkUp = false;
    _ethGotIP = false;
    break;
  case ARDUINO_EVENT_ETH_STOP:
    DEBUG_PRINTLN("[NET] Ethernet stopped");
    _ethLinkUp = false;
    _ethGotIP = false;
    break;
  default:
    break;
  }
}

// ── _initEthernet() ──────────────────────────────────────────────────────────
void NetManager::_initEthernet() {
  WiFi.onEvent(_ethEventHandler);
  ETH.begin(ETH_PHY_ADDR, ETH_PHY_POWER, ETH_PHY_MDC, ETH_PHY_MDIO,
            ETH_PHY_TYPE, ETH_CLK_MODE);

  // Wait up to WIFI_TIMEOUT_MS for IP
  uint32_t deadline = millis() + WIFI_TIMEOUT_MS;
  while (!_ethGotIP && millis() < deadline) {
    delay(250);
    DEBUG_PRINT(".");
  }
  DEBUG_PRINTLN();

  if (_ethGotIP) {
    _everConnected = true;
    DEBUG_PRINTF("[NET] Ethernet ready — IP: %s\n",
                 ETH.localIP().toString().c_str());
  } else {
    DEBUG_PRINTLN("[NET] WARN — Ethernet not ready within timeout. "
                  "Will retry in loop.");
  }
}

#else // WiFi

#include <esp_task_wdt.h> // for WDT suspend/resume around portal

// ── _initWiFi() — WiFiManager captive portal ─────────────────────────────────
//
// Behaviour:
//   1. First boot (no NVS credentials):
//        Opens soft-AP  "PPF-Monitor"  on 192.168.4.1.
//        User connects, enters factory WiFi SSID + password via browser.
//        Credentials saved to NVS flash → device reconnects automatically.
//
//   2. Subsequent boots (NVS credentials present):
//        Attempts connection silently.  Portal never opens unless forced.
//
//   3. Portal timeout (PROV_TIMEOUT_SEC):
//        If nobody saves credentials, WiFiManager closes the portal and
//        _initWiFi() returns.  Device will retry in ensureConnected().
//
// WDT note:
//   autoConnect() blocks for up to (connect_timeout + portal_timeout) seconds.
//   That total (15 + 120 = 135 s) exceeds WATCHDOG_TIMEOUT_SEC (90 s), so we
//   temporarily remove the main task from WDT monitoring for the duration of
//   the call, then re-arm it immediately after.
//
void NetManager::_initWiFi() {
  // 1. If no hardcoded SSID, skip direct connect and clear any stale NVS creds
  //    so the portal always opens for fresh provisioning.
  // 1. If hardcoded SSID is set, try direct connection first.
  if (strlen(WIFI_SSID) > 0) {
    DEBUG_PRINTF("[NET] Attempting direct connection to SSID: %s\n", WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    uint32_t startMs = millis();
    while (WiFi.status() != WL_CONNECTED &&
           (millis() - startMs < WIFI_TIMEOUT_MS)) {
      delay(500);
      DEBUG_PRINT(".");
    }
    DEBUG_PRINTLN();

    if (WiFi.status() == WL_CONNECTED) {
      _everConnected = true;
      DEBUG_PRINTF("[NET] WiFi connected directly — IP: %s\n",
                   WiFi.localIP().toString().c_str());
      return;
    }

    DEBUG_PRINTLN(
        "[NET] Direct connection failed. Starting WiFiManager portal...");
  } else {
    // No hardcoded SSID — WiFiManager will use saved NVS creds if available,
    // or open captive portal if no creds are saved / saved creds fail.
    DEBUG_PRINTLN("[NET] No hardcoded SSID — WiFiManager will handle connection");
  }

  // 2. Fall back to WiFiManager if direct connection fails.
  WiFiManager wm;
  wm.setDebugOutput(false);
  wm.setConnectTimeout(WIFI_TIMEOUT_MS / 1000);
  wm.setConfigPortalTimeout(PROV_TIMEOUT_SEC);

  DEBUG_PRINTF("[NET] Portal AP: '%s' (192.168.4.1)\n", PROV_AP_NAME);

  esp_task_wdt_delete(NULL);
  bool connected = (strlen(PROV_AP_PASSWORD) > 0)
                       ? wm.autoConnect(PROV_AP_NAME, PROV_AP_PASSWORD)
                       : wm.autoConnect(PROV_AP_NAME);

  // Re-arm WDT for normal operation.
  esp_task_wdt_add(NULL);
  esp_task_wdt_reset();

  if (connected) {
    _everConnected = true;
    DEBUG_PRINTF("[NET] WiFi connected — IP: %s  RSSI: %d dBm\n",
                 WiFi.localIP().toString().c_str(), WiFi.RSSI());
  } else {
    DEBUG_PRINTLN("[NET] WARN — Portal timed out, no credentials saved. "
                  "Will retry in loop.");
  }
}

#endif // USE_ETHERNET

// ─── begin() ─────────────────────────────────────────────────────────────────
void NetManager::begin() {
  DEBUG_PRINTF("[NET] Interface: %s\n", interfaceType());

#ifdef USE_ETHERNET
  _initEthernet();
#else
  _initWiFi();
#endif
}

// ─── ensureConnected() ───────────────────────────────────────────────────────
bool NetManager::ensureConnected() {
  if (isConnected())
    return true;

#ifdef USE_ETHERNET
  // Ethernet reconnect is handled by the event handler + ETH stack.
  // If _ethGotIP is still false, just wait — cable may be unplugged.
  if (!_ethGotIP) {
    DEBUG_PRINTLN("[NET] Ethernet waiting for IP…");
  }
  return _ethGotIP;

#else // WiFi
  uint32_t now = millis();
  if (now - _lastReconnectAttemptMs < MQTT_RECONNECT_DELAY_MS) {
    return false;
  }
  _lastReconnectAttemptMs = now;
  // Use reconnect() — honours credentials stored in NVS by WiFiManager,
  // rather than the hardcoded WIFI_SSID/WIFI_PASSWORD defines.
  DEBUG_PRINTLN("[NET] WiFi disconnected — reconnecting with NVS credentials…");
  WiFi.reconnect();
  return false; // caller will check again next iteration
#endif
}

// ─── isConnected() ───────────────────────────────────────────────────────────
bool NetManager::isConnected() const {
#ifdef USE_ETHERNET
  return _ethGotIP;
#else
  return WiFi.status() == WL_CONNECTED;
#endif
}

// ─── getIPAddress() ──────────────────────────────────────────────────────────
String NetManager::getIPAddress() const {
  if (!isConnected())
    return "0.0.0.0";
#ifdef USE_ETHERNET
  return ETH.localIP().toString();
#else
  return WiFi.localIP().toString();
#endif
}

// ─── interfaceType() ─────────────────────────────────────────────────────────
const char *NetManager::interfaceType() {
#ifdef USE_ETHERNET
  return "Ethernet (LAN8720A)";
#else
  return "WiFi";
#endif
}
