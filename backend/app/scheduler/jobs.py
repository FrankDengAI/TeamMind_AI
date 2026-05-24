"""APScheduler 定时任务 - 周期调优."""
import json
import logging

from app import db
from app.models import GroupInfo, Task
from app.services.algorithms.task_adjust import TaskAdjustAlgorithm

logger = logging.getLogger("teammind.scheduler")
adjuster = TaskAdjustAlgorithm()


def run_periodic_adjust(app=None):
    """对所有组执行动态任务调优."""
    if app is None:
        from flask import current_app

        app = current_app._get_current_object()
    with app.app_context():
        from app.models import BehaviorLog

        groups = GroupInfo.query.all()
        for group in groups:
            tasks = Task.query.filter_by(group_id=group.id).all()
            if not tasks:
                continue
            logs = BehaviorLog.query.filter_by(group_id=group.id).all()
            summary = adjuster.summarize_behavior(logs)
            members = []
            for mid in group.member_list():
                from app.models import UserProfile

                prof = UserProfile.query.filter_by(user_id=mid).order_by(UserProfile.create_time.desc()).first()
                if prof:
                    d = prof.to_dict()
                    d["user_id"] = mid
                    members.append(d)
            result = adjuster.adjust([t.to_dict() for t in tasks], summary, members)
            for t in tasks:
                for sug in result["suggestions"]:
                    if sug.get("task_id") == t.id:
                        t.pending_adjust = json.dumps(sug, ensure_ascii=False)
            logger.info("Adjusted group %s: %d suggestions", group.id, len(result["suggestions"]))
        db.session.commit()


def start_scheduler(app):
    """启动调度器."""
    if app.config.get("TESTING"):
        return None
    if app.extensions.get("teammind_scheduler"):
        return app.extensions["teammind_scheduler"]

    from apscheduler.schedulers.background import BackgroundScheduler

    days = app.config.get("DEFAULT_ADJUST_DAYS", 7)
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_periodic_adjust, "interval", days=days, id="task_adjust", args=[app], replace_existing=True)
    scheduler.start()
    app.extensions["teammind_scheduler"] = scheduler
    return scheduler
