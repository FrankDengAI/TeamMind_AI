"""生成可供手机扫码访问的局域网/公网入口 URL."""
from __future__ import annotations

import os
import socket
from typing import Any
def detect_lan_ip() -> str | None:
    """获取本机局域网 IPv4（用于手机同 WiFi 扫码）."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            if ip and not ip.startswith("127."):
                return ip
    except OSError:
        pass
    try:
        host = socket.gethostname()
        for info in socket.getaddrinfo(host, None, socket.AF_INET):
            ip = info[4][0]
            if ip and not ip.startswith("127."):
                return ip
    except OSError:
        pass
    return None


def build_access_urls(
    *,
    request_host: str | None = None,
    request_scheme: str = "http",
    port: int | str | None = None,
) -> dict[str, Any]:
    """
    构造门户 / 教师端 / 学生端 URL。
    优先 TEAMMIND_PUBLIC_URL；本机访问时尽量替换为局域网 IP 以便扫码。
    """
    public = (os.environ.get("TEAMMIND_PUBLIC_URL") or "").strip().rstrip("/")
    if public:
        base = public
        scan_ready = True
        source = "env"
    else:
        host = (request_host or "127.0.0.1").split(":")[0]
        port = str(port or os.environ.get("PORT", "5000"))
        if host in ("127.0.0.1", "localhost", "::1"):
            lan = detect_lan_ip()
            if lan:
                base = f"http://{lan}:{port}"
                scan_ready = True
                source = "lan"
            else:
                base = f"http://127.0.0.1:{port}"
                scan_ready = False
                source = "localhost"
        else:
            if ":" in host:
                base = f"{request_scheme}://{request_host}".rstrip("/")
            else:
                base = f"{request_scheme}://{host}:{port}"
            scan_ready = True
            source = "request"

    urls = {
        "portal": f"{base}/",
        "student": f"{base}/student/",
        "admin": f"{base}/admin/",
        "scan_page": f"{base}/scan/",
    }
    hint_zh = (
        "手机与电脑需在同一 WiFi；先运行 python main.py --host 0.0.0.0，再扫描下方二维码。"
        if scan_ready
        else "当前仅本机可访问。请使用 python main.py --host 0.0.0.0 启动，并确保手机与电脑同一 WiFi。"
    )
    hint_en = (
        "Phone and PC must be on the same Wi-Fi. Start with: python main.py --host 0.0.0.0"
        if scan_ready
        else "Localhost only. Run: python main.py --host 0.0.0.0 and use the same Wi-Fi."
    )
    return {
        "base": base,
        "urls": urls,
        "scan_ready": scan_ready,
        "source": source,
        "lan_ip": detect_lan_ip(),
        "hint_zh": hint_zh,
        "hint_en": hint_en,
    }
