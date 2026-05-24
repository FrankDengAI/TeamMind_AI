"""健康检查接口."""
from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)


@bp.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "组队超脑 TeamMind AI"})
