"""学习社区：富媒体帖子、互动与被动标签采集."""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db
from app.config import Config
from app.middleware.auth import get_request_user_id, admin_required, write_audit
from app.models import CommunityPost, PostComment, PostInteraction
from app.services.engines.deepseek_parser import DeepSeekParser
from app.services.entitlement_service import consume_ai_points, resolve_teacher_id_for_student
from app.services.passive_tag_pipeline import PassiveTagPipeline
from app.services.tag_catalog import normalize_active_tags

bp = Blueprint("community", __name__)
admin_bp = Blueprint("admin_community", __name__)
pipeline = PassiveTagPipeline()
deepseek = DeepSeekParser()


def _parse_json_field(value, default=None):
    if default is None:
        default = []
    if value in (None, ""):
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("JSON 字段格式错误") from exc


@bp.route("/feed", methods=["GET"])
@jwt_required()
def feed():
    uid = get_request_user_id()
    page = max(1, request.args.get("page", default=1, type=int))
    size = min(30, max(1, request.args.get("size", default=12, type=int)))
    q = CommunityPost.query.filter_by(status="published").order_by(CommunityPost.create_time.desc())
    posts = q.offset((page - 1) * size).limit(size).all()
    data = []
    for post in posts:
        item = post.to_dict(uid)
        item["stats"] = _post_stats(post.id)
        data.append(item)
    return jsonify({"items": data, "page": page, "size": size})


@bp.route("/posts", methods=["POST"])
@jwt_required()
def create_post():
    uid = get_request_user_id()
    body = request.get_json(silent=True) or {}
    title = (request.form.get("title") if request.form else None) or body.get("title", "")
    content = (request.form.get("content") if request.form else None) or body.get("content", "")
    is_anonymous = str((request.form.get("is_anonymous") if request.form else None) or body.get("is_anonymous", "false")).lower() in {"1", "true", "yes"}
    tags_raw = (request.form.get("tags") if request.form else None) or body.get("tags", "[]")
    try:
        tags = normalize_active_tags(_parse_json_field(tags_raw))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    content = (content or "").strip()
    if len(content) < 10:
        return jsonify({"error": "帖子内容至少 10 字"}), 400
    media = _save_media(uid)
    llm_tags = []
    teacher_id = resolve_teacher_id_for_student(uid)
    if teacher_id:
        try:
            consume_ai_points(teacher_id, "community.llm")
            analysis = deepseek.parse_profile(content, tags)
            llm_tags = (analysis.get("knowledge", {}).get("tags") or []) + (analysis.get("skill", {}).get("tags") or []) + (
                analysis.get("collaboration", {}).get("tags") or []
            )
        except Exception:
            llm_tags = []
    post = CommunityPost(
        user_id=uid,
        title=(title or "")[:160],
        content=content,
        media_json=json.dumps(media, ensure_ascii=False),
        tags_json=json.dumps(tags, ensure_ascii=False),
        is_anonymous=is_anonymous,
        status="published",
        llm_tags_json=json.dumps(llm_tags, ensure_ascii=False),
    )
    db.session.add(post)
    db.session.commit()
    write_audit("community_post_create", "community_post", post.id)
    return jsonify(post.to_dict(uid)), 201


@bp.route("/posts/<int:post_id>", methods=["GET"])
@jwt_required()
def get_post(post_id):
    uid = get_request_user_id()
    post = CommunityPost.query.get_or_404(post_id)
    if post.status != "published":
        return jsonify({"error": "帖子不可见"}), 404
    pipeline.record_post_event(uid, post, "post_view")
    db.session.commit()
    data = post.to_dict(uid)
    data["stats"] = _post_stats(post.id)
    data["comments"] = [c.to_dict() for c in PostComment.query.filter_by(post_id=post.id).order_by(PostComment.create_time.asc()).all()]
    return jsonify(data)


def _published_post_or_404(post_id: int):
    post = CommunityPost.query.get_or_404(post_id)
    if post.status != "published":
        return None
    return post


@bp.route("/posts/<int:post_id>/like", methods=["POST", "DELETE"])
@jwt_required()
def like_post(post_id):
    uid = get_request_user_id()
    post = _published_post_or_404(post_id)
    if not post:
        return jsonify({"error": "帖子不可见"}), 404
    if request.method == "DELETE":
        PostInteraction.query.filter_by(user_id=uid, post_id=post_id, type="post_like").delete()
        db.session.commit()
        return jsonify({"ok": True})
    existing = PostInteraction.query.filter_by(user_id=uid, post_id=post_id, type="post_like").first()
    if existing:
        return jsonify({"ok": True, "stats": _post_stats(post_id)})
    pipeline.record_post_event(uid, post, "post_like")
    db.session.commit()
    return jsonify({"ok": True, "stats": _post_stats(post_id)})


@bp.route("/posts/<int:post_id>/favorite", methods=["POST"])
@jwt_required()
def favorite_post(post_id):
    uid = get_request_user_id()
    post = _published_post_or_404(post_id)
    if not post:
        return jsonify({"error": "帖子不可见"}), 404
    existing = PostInteraction.query.filter_by(user_id=uid, post_id=post_id, type="post_favorite").first()
    if existing:
        return jsonify({"ok": True, "stats": _post_stats(post_id)})
    pipeline.record_post_event(uid, post, "post_favorite")
    db.session.commit()
    return jsonify({"ok": True, "stats": _post_stats(post_id)})


@bp.route("/posts/<int:post_id>/comment", methods=["POST"])
@jwt_required()
def comment_post(post_id):
    uid = get_request_user_id()
    post = _published_post_or_404(post_id)
    if not post:
        return jsonify({"error": "帖子不可见"}), 404
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"error": "评论不能为空"}), 400
    comment = PostComment(post_id=post_id, user_id=uid, content=content, is_anonymous=bool(data.get("is_anonymous")))
    db.session.add(comment)
    db.session.flush()
    pipeline.record_post_event(uid, post, "post_comment", {"comment_id": comment.id})
    db.session.commit()
    return jsonify(comment.to_dict()), 201


@admin_bp.route("/community/posts", methods=["GET"])
@admin_required
def admin_posts():
    posts = CommunityPost.query.order_by(CommunityPost.create_time.desc()).limit(200).all()
    data = []
    for post in posts:
        item = post.to_dict()
        item["stats"] = _post_stats(post.id)
        data.append(item)
    return jsonify(data)


@admin_bp.route("/community/posts/<int:post_id>/status", methods=["PUT"])
@admin_required
def admin_post_status(post_id):
    post = CommunityPost.query.get_or_404(post_id)
    data = request.get_json(silent=True) or {}
    post.status = data.get("status") or post.status
    db.session.commit()
    return jsonify(post.to_dict())


def _post_stats(post_id: int) -> dict:
    return {
        "likes": PostInteraction.query.filter_by(post_id=post_id, type="post_like").with_entities(PostInteraction.user_id).distinct().count(),
        "favorites": PostInteraction.query.filter_by(post_id=post_id, type="post_favorite").with_entities(PostInteraction.user_id).distinct().count(),
        "comments": PostComment.query.filter_by(post_id=post_id).count(),
    }


def _save_media(uid: int) -> list[dict]:
    if not request.files:
        return []
    base = Path(Config.UPLOAD_FOLDER) / "posts" / str(uid)
    base.mkdir(parents=True, exist_ok=True)
    saved = []
    for f in request.files.getlist("media"):
        name = f.filename or ""
        ext = Path(name).suffix.lower()
        content = f.read()
        if ext in Config.ALLOWED_IMAGE_EXT:
            if len(content) > Config.MAX_IMAGE_SIZE:
                continue
            mtype = "image"
        elif ext in Config.ALLOWED_VIDEO_EXT:
            if len(content) > Config.MAX_VIDEO_SIZE:
                continue
            mtype = "video"
        else:
            continue
        filename = f"{uuid.uuid4().hex}{ext}"
        path = base / filename
        path.write_bytes(content)
        rel = f"posts/{uid}/{filename}"
        saved.append({"type": mtype, "url": request.host_url.rstrip("/") + f"/uploads/{rel}", "name": name})
        if len([x for x in saved if x["type"] == "image"]) >= current_app.config.get("MAX_POST_IMAGES", 9):
            break
    return saved
