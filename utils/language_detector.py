import os

_EXT_MAP = {
    ".py": "Python",
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".h": "C++", ".hpp": "C++",
    ".java": "Java",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".html": "HTML/CSS", ".css": "HTML/CSS",
}

def detect_language(path: str) -> str:
    if os.path.isfile(path):
        return _EXT_MAP.get(os.path.splitext(path)[1].lower(), "其他")
    counts = {}
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                lang = _EXT_MAP.get(os.path.splitext(entry.name)[1].lower())
                if lang:
                    counts[lang] = counts.get(lang, 0) + 1
    except OSError:
        pass
    return max(counts, key=counts.get) if counts else "其他"
