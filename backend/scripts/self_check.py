"""TeamMind AI 系统自检脚本."""
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "backend"))

BASE = "http://127.0.0.1:5000"
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append({"name": name, "ok": ok, "detail": detail})
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: {detail}")


def main():
    print("=== TeamMind AI 系统自检 ===\n")
    try:
        r = httpx.get(f"{BASE}/api/health", timeout=5)
        check("健康检查", r.status_code == 200, str(r.json())[:80])
    except Exception as e:
        check("健康检查", False, f"服务未启动: {e}")
        _save_and_exit(1)

    # 登录
    r = httpx.post(f"{BASE}/api/auth/login", json={"account": "admin", "password": "admin123"})
    check("管理员登录", r.status_code == 200)
    if r.status_code != 200:
        _save_and_exit(1)
    token = r.json()["token"]
    h = {"Authorization": f"Bearer {token}"}

    text = (
        "计算机本科生，熟悉Python、Java、MySQL、Git，擅长软件工程与后端开发，"
        "团队协作中担任技术开发，沟通能力强，风格积极主动。"
    ) * 2
    r = httpx.post(f"{BASE}/api/profile/parse", json={"raw_text": text}, headers=h)
    check("文本解析", r.status_code == 200 and r.json().get("profile", {}).get("skill_score", 0) > 0)

    from app.services.algorithms.grouping import GroupingAlgorithm

    profiles = []
    for i in range(12):
        profiles.append(
            {
                "user_id": i + 1,
                "skill_score": 5 + i % 4,
                "knowledge_score": 6,
                "collab_score": 7,
                "major": ["计算机", "金融", "设计"][i % 3],
                "pref_role": ["技术开发", "设计执行", "数据支持"][i % 3],
                "tech_skills": ["Python"],
                "collab_style": ["积极主动"],
            }
        )
    gr = GroupingAlgorithm().create_groups(profiles, group_size=4)
    diff = max(g["avg_skill"] for g in gr["groups"]) - min(g["avg_skill"] for g in gr["groups"])
    check("分组算法", diff <= 3, f"skill diff={diff}")

    r = httpx.get(f"{BASE}/api/board/sync", headers=h)
    check("看板同步", r.status_code == 200)

    import concurrent.futures

    def hit():
        return httpx.get(f"{BASE}/api/health", timeout=5).status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        codes = list(ex.map(lambda _: hit(), range(10)))
    check("并发10", all(c == 200 for c in codes))

    _save_and_exit(0 if all(x["ok"] for x in RESULTS) else 1)


def _save_and_exit(code):
    out = ROOT / "docs" / "self_check_latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(RESULTS, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n结果已保存: {out}")
    sys.exit(code)


if __name__ == "__main__":
    main()
