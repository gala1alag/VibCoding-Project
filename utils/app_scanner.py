import os
import threading
from typing import Optional
import win32com.client
from core.database import get_connection


def _resolve_lnk(lnk_path: str) -> Optional[str]:
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(lnk_path)
        target = shortcut.Targetpath
        return target if target and os.path.exists(target) else None
    except Exception:
        return None


def _collect() -> list[dict]:
    apps = {}  # path -> name，去重

    # 开始菜单 + 桌面 .lnk
    lnk_roots = [
        os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu"),
        os.path.join(os.environ.get("PROGRAMDATA", ""), r"Microsoft\Windows\Start Menu"),
        os.path.join(os.environ.get("USERPROFILE", ""), "Desktop"),
        os.path.join(os.environ.get("PUBLIC", ""), "Desktop"),
    ]
    for root in lnk_roots:
        if not os.path.isdir(root):
            continue
        for dirpath, _, files in os.walk(root):
            for f in files:
                if f.lower().endswith(".lnk"):
                    target = _resolve_lnk(os.path.join(dirpath, f))
                    if target and target.lower().endswith(".exe") and target not in apps:
                        apps[target] = os.path.splitext(f)[0]

    # Program Files 一级子目录 .exe
    for env in ("PROGRAMFILES", "PROGRAMFILES(X86)"):
        root = os.environ.get(env, "")
        if not os.path.isdir(root):
            continue
        try:
            for entry in os.scandir(root):
                if not entry.is_dir():
                    continue
                try:
                    for f in os.scandir(entry.path):
                        if f.is_file() and f.name.lower().endswith(".exe") and f.path not in apps:
                            apps[f.path] = os.path.splitext(f.name)[0]
                except OSError:
                    pass
        except OSError:
            pass

    return [{"name": name, "path": path} for path, name in apps.items()]


def _save(apps: list[dict]) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM app_index")
        conn.executemany(
            "INSERT INTO app_index (name, path) VALUES (?, ?)",
            [(a["name"], a["path"]) for a in apps]
        )
        conn.commit()
    finally:
        conn.close()


def scan_apps(on_done=None) -> None:
    def _run():
        apps = _collect()
        _save(apps)
        if on_done:
            on_done()
    threading.Thread(target=_run, daemon=True).start()


def get_cached_apps() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT name, path FROM app_index ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
