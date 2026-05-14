import subprocess
from datetime import datetime
from core.database import get_connection
from utils.language_detector import detect_language
from utils.editor_detector import get_editors_for_language
from core.settings import Settings


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class ProjectCtrl:
    def get_all(self, language_filter: str = None) -> list:
        conn = get_connection()
        try:
            if language_filter and language_filter != "全部":
                rows = conn.execute(
                    "SELECT * FROM projects WHERE language=? ORDER BY last_opened_at DESC",
                    (language_filter,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM projects ORDER BY last_opened_at DESC"
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_by_id(self, project_id: int) -> dict:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM projects WHERE id=?", (project_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def add(self, name: str, path: str, type_: str) -> int:
        language = detect_language(path)
        conn = get_connection()
        try:
            cur = conn.execute(
                "INSERT INTO projects (name, path, type, language, created_at) VALUES (?,?,?,?,?)",
                (name, path, type_, language, _now())
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def update(self, project_id: int, **fields) -> None:
        allowed = {"name", "language", "color", "memo", "note", "default_editor"}
        data = {k: v for k, v in fields.items() if k in allowed}
        if not data:
            return
        sets = ", ".join(f"{k}=?" for k in data)
        conn = get_connection()
        try:
            conn.execute(
                f"UPDATE projects SET {sets} WHERE id=?",
                (*data.values(), project_id)
            )
            conn.commit()
        finally:
            conn.close()

    def delete(self, project_id: int) -> None:
        conn = get_connection()
        try:
            conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
            conn.commit()
        finally:
            conn.close()

    def open_in_editor(self, project: dict, editor_path: str) -> None:
        subprocess.Popen([editor_path, project["path"]])
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE projects SET last_opened_at=? WHERE id=?",
                (_now(), project["id"])
            )
            conn.commit()
        finally:
            conn.close()

    def get_editors_for_project(self, project: dict) -> list:
        settings = Settings()
        editor_map = settings.get("editor_map") or {}
        return get_editors_for_language(project.get("language", ""), editor_map)
