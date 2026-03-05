"""
Module: camera_discovery.py
Purpose:
    Camera auto-discovery via MediaMTX API and network probing.
    Queries the MediaMTX REST API for active stream paths and registers
    any new cameras found.

Author: PPF Monitoring Team
Created: 2026-03-05
"""

import asyncio
from typing import Optional

import httpx

from src.utils.logger import get_logger

logger = get_logger(__name__)

# MediaMTX REST API default port
MEDIAMTX_API_PORT = 9997
PROBE_TIMEOUT = 3.0


async def query_mediamtx_paths(host: str, api_port: int = MEDIAMTX_API_PORT) -> list[dict]:
    """
    Query MediaMTX /v3/paths/list to find active stream paths.

    Returns list of dicts with keys: name, source_type, ready, readers, etc.
    """
    url = f"http://{host}:{api_port}/v3/paths/list"
    try:
        async with httpx.AsyncClient(timeout=PROBE_TIMEOUT) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items") or []
            logger.info(f"MediaMTX at {host}: found {len(items)} path(s)")
            return items
    except httpx.ConnectError:
        logger.warning(f"MediaMTX at {host}:{api_port} unreachable")
        return []
    except Exception as e:
        logger.error(f"MediaMTX query failed ({host}): {e}")
        return []


def build_stream_urls(host: str, path_name: str, ports: Optional[dict] = None) -> dict:
    """Build stream URL dict from a MediaMTX path."""
    rtsp_port = (ports or {}).get("rtsp", 8554)
    hls_port = (ports or {}).get("hls", 8888)
    webrtc_port = (ports or {}).get("webrtc", 8889)

    return {
        "rtsp": {"main": f"rtsp://{host}:{rtsp_port}/{path_name}"},
        "hls": {"main": f"http://{host}:{hls_port}/{path_name}"},
        "webrtc": {"main": f"http://{host}:{webrtc_port}/{path_name}"},
    }


async def probe_rtsp_port(host: str, port: int = 554) -> bool:
    """Quick TCP connect probe to check if an RTSP port is open."""
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=PROBE_TIMEOUT,
        )
        writer.close()
        await writer.wait_closed()
        return True
    except (asyncio.TimeoutError, OSError):
        return False


async def discover_mediamtx_cameras(
    mediamtx_host: str,
    mediamtx_ports: Optional[dict] = None,
    api_port: int = MEDIAMTX_API_PORT,
) -> list[dict]:
    """
    Discover cameras by querying a MediaMTX instance.

    Returns list of camera-like dicts ready for registration:
      device_id, name, ip_address, camera_type, stream_urls, is_online, discovered_via
    """
    paths = await query_mediamtx_paths(mediamtx_host, api_port)
    cameras = []

    for path in paths:
        path_name = path.get("name", "")
        if not path_name:
            continue

        ready = path.get("ready", False)
        source = path.get("source", {}) or {}
        source_type = source.get("type", "unknown")

        cameras.append({
            "device_id": f"mtx-{mediamtx_host}-{path_name}".replace("/", "-"),
            "name": f"MediaMTX: {path_name}",
            "ip_address": mediamtx_host,
            "camera_type": "raspberry_pi" if "rpi" in path_name.lower() else "ip_camera",
            "stream_urls": build_stream_urls(mediamtx_host, path_name, mediamtx_ports),
            "is_online": ready,
            "discovered_via": "scan",
            "source_type": source_type,
        })

    return cameras
