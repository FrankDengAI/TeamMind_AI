"""扫码访问：返回局域网入口与二维码 SVG."""
from __future__ import annotations

import io

from flask import Blueprint, jsonify, request, Response

from app.services.access_urls import build_access_urls

bp = Blueprint("access", __name__)


def _access_payload() -> dict:
    host = request.host or "127.0.0.1:5000"
    port = request.environ.get("SERVER_PORT") or host.split(":")[-1]
    return build_access_urls(
        request_host=host,
        request_scheme=request.scheme,
        port=port,
    )


@bp.route("/api/access/urls", methods=["GET"])
def access_urls():
    return jsonify(_access_payload())


@bp.route("/api/access/qrcode.svg", methods=["GET"])
def access_qrcode_svg():
    """生成指定入口的二维码 SVG（target=portal|student|admin|scan）."""
    target = (request.args.get("target") or "portal").strip().lower()
    payload = _access_payload()
    urls = payload["urls"]
    url = urls.get(target) or urls.get("portal")
    try:
        import qrcode
        from qrcode.image.svg import SvgImage

        buf = io.BytesIO()
        img = qrcode.make(url, image_factory=SvgImage)
        img.save(buf)
        body = buf.getvalue()
        if not isinstance(body, bytes):
            body = str(body).encode("utf-8")
        return Response(body, mimetype="image/svg+xml")
    except ImportError:
        return jsonify({"error": "请安装 qrcode：pip install qrcode", "url": url}), 503
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc), "url": url}), 500
