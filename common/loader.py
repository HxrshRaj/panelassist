"""Loads a mock (or real) submission folder into a plain dict."""
import json
import os


def load_submission(path: str) -> dict:
    def read(name, default=""):
        p = os.path.join(path, name)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return f.read()
        return default

    manifest = {}
    manifest_path = os.path.join(path, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)

    trajectory = {}
    traj_path = os.path.join(path, "trajectory.json")
    if os.path.exists(traj_path):
        with open(traj_path, encoding="utf-8") as f:
            trajectory = json.load(f)

    return {
        "slug": os.path.basename(path.rstrip("/")),
        "readme": read("README.md"),
        "reproduce": read("REPRODUCE.md"),
        "manifest": manifest,
        "trajectory": trajectory,
        "trajectory_raw": json.dumps(trajectory, indent=2) if trajectory else "",
    }


def load_all_submissions(root: str) -> list:
    out = []
    for name in sorted(os.listdir(root)):
        full = os.path.join(root, name)
        if os.path.isdir(full):
            out.append(load_submission(full))
    return out


def full_text(sub: dict) -> str:
    """Everything a naive single-prompt baseline would be handed."""
    files_list = "\n".join(sub["manifest"].get("files", []))
    return (
        f"=== README.md ===\n{sub['readme']}\n\n"
        f"=== REPRODUCE.md ===\n{sub['reproduce']}\n\n"
        f"=== Files present in the submission (from repo listing) ===\n{files_list}\n\n"
        f"=== Agent trajectory log ===\n{sub['trajectory_raw']}\n"
    )
