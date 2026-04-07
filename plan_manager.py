import os
import json
import time

PLANS_DIR = ".plans"


def ensure_plans_dir():
    os.makedirs(PLANS_DIR, exist_ok=True)


def save_plan(name: str, task: str, plan_text: str) -> str:
    ensure_plans_dir()
    plan = {
        "name": name,
        "task": task,
        "plan": plan_text,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pending",
    }
    path = os.path.join(PLANS_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)
    return path


def load_plan(name: str) -> dict | None:
    path = os.path.join(PLANS_DIR, f"{name}.json")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_plans() -> list[dict]:
    ensure_plans_dir()
    plans = []
    for fname in sorted(os.listdir(PLANS_DIR)):
        if fname.endswith(".json"):
            path = os.path.join(PLANS_DIR, fname)
            with open(path, "r", encoding="utf-8") as f:
                plan = json.load(f)
                plan["filename"] = fname
                plans.append(plan)
    return plans


def get_latest_plan() -> dict | None:
    plans = list_plans()
    pending = [p for p in plans if p.get("status") == "pending"]
    if pending:
        return pending[-1]
    return plans[-1] if plans else None


def mark_plan_done(name: str) -> None:
    path = os.path.join(PLANS_DIR, f"{name}.json")
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            plan = json.load(f)
        plan["status"] = "done"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2)
