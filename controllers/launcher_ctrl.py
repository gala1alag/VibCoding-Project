import subprocess
from datetime import datetime
from core.database import get_connection
from utils.app_scanner import scan_apps, get_cached_apps
from utils.fuzzy_matcher import match


class LauncherCtrl:
    def start_scan(self, on_done=None) -> None:
        scan_apps(on_done=on_done)

    def search(self, query: str) -> list:
        return match(query, get_cached_apps())

    def launch(self, app: dict) -> None:
        subprocess.Popen([app["path"]])
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE app_index SET last_scanned_at=? WHERE path=?",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), app["path"])
            )
            conn.commit()
        finally:
            conn.close()
