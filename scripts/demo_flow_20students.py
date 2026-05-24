"""
20 人全流程答辩演示脚本（HTTP API 自动化）

步骤：注册/登录 20 学员 → 提交画像 → 管理员分组 → 分配角色 → 分配任务 → 模拟进度

用法:
  python scripts/demo_flow_20students.py
  python scripts/demo_flow_20students.py --reset
  python scripts/demo_flow_20students.py --group-size 5 --base-url http://127.0.0.1:5000
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE = "http://127.0.0.1:5000"
STUDENT_PASSWORD = "123456"
ADMIN_ACCOUNT = ("admin", "admin123")

ROLES = ["技术开发", "设计执行", "数据支持", "协调推进", "文档撰写"]
MAJORS = ["计算机", "软件工程", "数据科学", "产品设计", "信息管理"]


def student_text(i: int) -> str:
    role = ROLES[i % len(ROLES)]
    major = MAJORS[i % len(MAJORS)]
    return (
        f"我是{major}专业大三学生student{i:02d}，擅长{role}相关实践，"
        f"熟悉 Python 与团队协作，沟通积极，希望在本学期项目中承担{role}工作，"
        f"能按时交付并主动同步进度，愿意与队友分工配合完成课程设计目标。"
    )


def step(msg: str) -> None:
    print(f"\n>>> {msg}")


def main() -> int:
    parser = argparse.ArgumentParser(description="TeamMind 20 人全流程演示")
    parser.add_argument("--base-url", default=DEFAULT_BASE, help="后台 API 根地址（不含 /api）")
    parser.add_argument("--reset", action="store_true", help="重建数据库（会清空现有数据）")
    parser.add_argument("--group-size", type=int, default=4, choices=[3, 4, 5, 6])
    parser.add_argument("--template", default="product_dev", help="任务模板 key")
    args = parser.parse_args()

    api = f"{args.base_url.rstrip('/')}/api"
    client = httpx.Client(timeout=60)

    try:
        r = client.get(f"{api}/health")
        r.raise_for_status()
    except Exception as e:
        print(f"后台未就绪，请先运行: python main.py\n  错误: {e}")
        return 1

    if args.reset:
        step("重建数据库")
        subprocess.run([sys.executable, str(ROOT / "database" / "init_db.py")], check=True, cwd=str(ROOT))

    tokens: dict[str, str] = {}
    student_ids: list[int] = []

    step("1/7 创建或登录 20 名学员")
    for i in range(1, 21):
        account = f"student{i:02d}"
        name = f"学员{i:02d}"
        body = {"account": account, "password": STUDENT_PASSWORD, "name": name}
        r = client.post(f"{api}/auth/register", json=body)
        if r.status_code not in (200, 201):
            r = client.post(f"{api}/auth/login", json={"account": account, "password": STUDENT_PASSWORD})
        if r.status_code not in (200, 201):
            print(f"  失败 {account}: {r.status_code} {r.text[:200]}")
            return 1
        data = r.json()
        tokens[account] = data["token"]
        student_ids.append(data["user"]["id"])
        print(f"  OK {account} (id={data['user']['id']})")

    step("2/7 每人提交能力画像")
    for i in range(1, 21):
        account = f"student{i:02d}"
        h = {"Authorization": f"Bearer {tokens[account]}"}
        text = student_text(i)
        r = client.post(f"{api}/profile/parse", json={"raw_text": text}, headers=h)
        if r.status_code != 200:
            print(f"  画像失败 {account}: {r.text[:200]}")
            return 1
    print("  20 份画像已生成")

    step("3/7 管理员登录并 AI 分组")
    r = client.post(
        f"{api}/auth/login",
        json={"account": ADMIN_ACCOUNT[0], "password": ADMIN_ACCOUNT[1]},
    )
    if r.status_code != 200:
        print("管理员登录失败，请确认 init_db 已执行")
        return 1
    admin_h = {"Authorization": f"Bearer {r.json()['token']}"}

    r = client.post(
        f"{api}/admin/ops/create-groups",
        json={"group_size": args.group_size, "user_ids": student_ids},
        headers=admin_h,
    )
    if r.status_code != 200:
        print(f"分组失败: {r.text[:300]}")
        return 1
    groups = r.json().get("groups") or []
    print(f"  已创建 {len(groups)} 个小组（每组约 {args.group_size} 人），均衡分 {r.json().get('balance_score')}")

    step("4/7 为各组分配组内角色")
    role_ok = 0
    r = client.post(f"{api}/admin/ops/assign-roles-all", headers=admin_h)
    if r.status_code == 200:
        role_ok = len(r.json().get("groups") or [])
    else:
        for g in groups:
            r1 = client.post(
                f"{api}/admin/ops/assign-roles",
                json={"group_id": g["id"]},
                headers=admin_h,
            )
            if r1.status_code == 200:
                role_ok += 1
        if role_ok == 0:
            print(f"角色分配失败（请重启 python main.py 以加载最新 API）: {r.text[:200]}")
            return 1
    print(f"  角色已分配：{role_ok} 个小组")

    step("5/7 为各组分配项目任务")
    for g in groups:
        gid = g["id"]
        r = client.post(
            f"{api}/admin/ops/assign-tasks",
            json={"group_id": gid, "template_key": args.template},
            headers=admin_h,
        )
        if r.status_code != 200:
            print(f"  组 {gid} 任务失败: {r.text[:200]}")
            return 1
        n = len(r.json().get("tasks") or [])
        print(f"  组 {g.get('group_name')} (id={gid}): {n} 个任务")

    step("6/7 模拟部分学员更新任务进度")
    progress_count = 0
    for idx, account in enumerate([f"student{i:02d}" for i in (1, 3, 5, 7, 9, 11)]):
        h = {"Authorization": f"Bearer {tokens[account]}"}
        r = client.get(f"{api}/board/personal", headers=h)
        if r.status_code != 200:
            continue
        tasks = r.json().get("tasks") or []
        for t in tasks[:2]:
            prog = 30 + idx * 10
            tr = client.post(
                f"{api}/task/{t['id']}/progress",
                json={"progress": min(100, prog), "submit_status": "on_time"},
                headers=h,
            )
            if tr.status_code == 200:
                progress_count += 1
    print(f"  已更新 {progress_count} 条任务进度")

    step("7/7 汇总（答辩演示入口）")
    r = client.get(f"{api}/admin/dashboard", headers=admin_h)
    platform = r.json().get("platform") or {} if r.status_code == 200 else {}
    alerts = platform.get("alerts") or []
    print("\n" + "=" * 60)
    print("答辩演示入口")
    print(f"  管理后台: {args.base_url}/")
    print(f"  学员端:   {args.base_url.rstrip('/')}/student/")
    print(f"  管理员:   {ADMIN_ACCOUNT[0]} / {ADMIN_ACCOUNT[1]}")
    print(f"  学员示例: student01 / {STUDENT_PASSWORD}")
    print("-" * 60)
    print(f"小组数: {len(groups)}  |  平台预警条数: {len(alerts)}")
    for g in groups:
        gid = g["id"]
        r2 = client.get(f"{api}/admin/team/{gid}/dashboard", headers=admin_h)
        dash = r2.json() if r2.status_code == 200 else {}
        members = dash.get("members") or []
        names = []
        for m in members:
            u = m.get("user") or {}
            names.append(f"{u.get('name')}({m.get('team_role', '?')})")
        rate = (dash.get("summary") or {}).get("completion_rate", "—")
        print(f"  [{g.get('group_name')}] 完成率 {rate}% — {', '.join(names)}")
    print("=" * 60)
    print("\n建议演示路径：管理端「项目工作台」步骤 1→5；学员端「填写画像→我的团队→我的任务」")
    return 0


if __name__ == "__main__":
    sys.exit(main())
