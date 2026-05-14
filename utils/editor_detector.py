import os
import winreg
from collections import namedtuple

EditorInfo = namedtuple("EditorInfo", ["name", "path"])

_TARGETS = {
    "Code.exe":       "VS Code",
    "Cursor.exe":     "Cursor",
    "pycharm64.exe":  "PyCharm",
    "qtcreator.exe":  "Qt Creator",
    "devenv.exe":     "Visual Studio",
    "notepad++.exe":  "Notepad++",
}

_LANG_PRIORITY = {
    "Python":     ["PyCharm", "VS Code", "Cursor"],
    "C++":        ["Qt Creator", "Visual Studio", "VS Code"],
    "JavaScript": ["VS Code", "Cursor"],
    "TypeScript": ["VS Code", "Cursor"],
}
_DEFAULT_PRIORITY = ["VS Code", "Cursor", "Notepad++"]


def _scan_dirs() -> dict:
    found = {}
    roots = [
        os.environ.get("PROGRAMFILES", "C:/Program Files"),
        os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)"),
        os.environ.get("LOCALAPPDATA", ""),
    ]
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        try:
            for entry in os.scandir(root):
                if not entry.is_dir():
                    continue
                for exe, name in _TARGETS.items():
                    candidate = os.path.join(entry.path, exe)
                    if os.path.isfile(candidate) and name not in found:
                        found[name] = candidate
        except OSError:
            pass
    return found


def _scan_registry() -> dict:
    found = {}
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"
        )
        i = 0
        while True:
            try:
                subname = winreg.EnumKey(key, i)
                i += 1
                for exe, name in _TARGETS.items():
                    if subname.lower() == exe.lower():
                        sub = winreg.OpenKey(key, subname)
                        val, _ = winreg.QueryValueEx(sub, "")
                        if val and os.path.isfile(val) and name not in found:
                            found[name] = val
                        winreg.CloseKey(sub)
            except OSError:
                break
        winreg.CloseKey(key)
    except OSError:
        pass
    return found


def scan() -> dict:
    found = _scan_dirs()
    found.update(_scan_registry())
    return found


def get_editors_for_language(language: str, settings_editor_map: dict = None) -> list:
    found = scan()
    priority = (
        (settings_editor_map or {}).get(language)
        or _LANG_PRIORITY.get(language, _DEFAULT_PRIORITY)
    )
    result = [EditorInfo(name, found[name]) for name in priority if name in found]
    for name, path in found.items():
        if not any(e.name == name for e in result):
            result.append(EditorInfo(name, path))
    return result
