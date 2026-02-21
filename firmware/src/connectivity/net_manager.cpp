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

static constexpr int ETH_PHY_ADDR  = 0;
static constexpr int ETH_PHY_POWER = -1;   // no power pin on this board
static constexpr int ETH_PHY_MDC   = 23;
static constexpr int ETH_PHY_MDIO  = 18;
static constexpr eth_clock_mode_t ETH_CLK_MODE = ETH_CLOCK_GPIO17_OUT;
static constexpr eth_phy_type_t   ETH_PHY_TYPE = ETH_PHY_LAN8720;

volatile bool NetManager::_ethLinkUp = false;
volatile bool NetManager::_ethGotIP  = false;

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
                         ETH.localIP().toString().c_str(),
                         ETH.linkSpeed(),
                         ETH.fullDuplex() ? "full" : "half");
            _ethGotIP = true;
            break;
        case ARDUINO_EVENT_ETH_DISCONNECTED:
            DEBUG_PRINTLN("[NET] Ethernet disconnected");
            _ethLinkUp = false;
            _ethGotIP  = false;
            break;
        case ARDUINO_EVENT_ETH_STOP:
            DEBUG_PRINTLN("[NET] Ethernet stopped");
            _ethLinkUp = false;
            _ethGotIP  = false;
            break;
        default:
            break;
    }
}

// ── _initEthernet() ──────────────────────────────────────────────────────────
void NetManager::_initEthernet() {
    WiFi.onEvent(_ethEventHandler);
    ETH.begin(ETH_PHY_ADDR,
              ETH_PHY_POWER,
              ETH_PHY_MDC,
              ETH_PHY_MDIO,
              ETH_PHY_TYPE,
              ETH_CLK_MODE);

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

#else  // WiFi

// ── _initWiFi() ──────────────────────────────────────────────────────────────
void NetManager::_initWiFi() {
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    DEBUG_PRINTF("[NET] Connecting to WiFi SSID: %s\n", WIFI_SSID);

    uint32_t deadline = millis() + WIFI_TIMEOUT_MS;
    while (WiFi.status() != WL_CONNECTED && millis() < deadline) {
        delay(500);
        DEBUG_PRINT(".");
    }
    DEBUG_PRINTLN();

    if (WiFi.status() == WL_CONNECTED) {
        _everConnected = true;
        DEBUG_PRINTF("[NET] WiFi connected — IP: %s  RSSI: %d dBm\n",
                     WiFi.localIP().toString().c_str(),
                     WiFi.RSSI());
    } else {
        DEBUG_PRINTLN("[NET] WARN — WiFi not connected within timeout. "
                      "Will retry in loop.");
    }
}

#endif  // USE_ETHERNET


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
    if (isConnected()) return true;

#ifdef USE_ETHERNET
    // Ethernet reconnect is handled by the event handler + ETH stack.
    // If _ethGotIP is still false, just wait — cable may be unplugged.
    if (!_ethGotIP) {
        DEBUG_PRINTLN("[NET] Ethernet waiting for IP…");
    }
    return _ethGotIP;

#else  // WiFi
    uint32_t now = millis();
    if (now - _lastReconnectAttemptMs < MQTT_RECONNECT_DELAY_MS) {
        return false;
    }
    _lastReconnectAttemptMs = now;
    DEBUG_PRINTF("[NET] WiFi reconnecting to %s…\n", WIFI_SSID);
    WiFi.disconnect();
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    return false;  // caller will check again next iteration
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
    if (!isConnected()) return "0.0.0.0";
#ifdef USE_ETHERNET
    return ETH.localIP().toString();
#else
    return WiFi.localIP().toString();
#endif
}


// ─── interfaceType() ─────────────────────────────────────────────────────────
const char* NetManager::interfaceType() {
#ifdef USE_ETHERNET
    return "Ethernet (LAN8720A)";
#else
    return "WiFi";
#endif
}
