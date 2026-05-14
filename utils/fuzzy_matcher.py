from rapidfuzz import process, fuzz


def match(query: str, candidates: list[dict], limit: int = 10) -> list[dict]:
    if not query:
        return candidates[:limit]
    names = [c["name"] for c in candidates]
    results = process.extract(query, names, scorer=fuzz.WRatio, limit=limit, score_cutoff=40)
    idx_map = {name: i for i, name in enumerate(names)}
    return [candidates[idx_map[name]] for name, score, _ in results]
